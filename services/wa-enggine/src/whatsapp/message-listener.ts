import type { WASocket, WAMessage } from "@whiskeysockets/baileys";
import { sendChatToAI } from "../ai/ai-client";
import { buildAIChatPayload } from "../ai/ai-payload";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import {
  extractMessageText,
  getChatType,
  getMessageKinds,
} from "./message-parser";
import { shouldProcessMessage } from "./trigger";
import { sendWhatsAppReply } from "./reply-context";
import { sendTextMessage } from "./message-sender";
import { createTraceId, maskJid } from "../utils/observability";
import { isProcessableChatType } from "../types/chat";
import { cacheMessage } from "./socket-state";

const botSentMessageIds = new Set<string>();
const MAX_TRACKED_BOT_MESSAGES = 500;

export function registerMessageListener(sock: WASocket): void {
  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    logger.info(
      {
        step: "message_upsert",
        type,
        count: messages.length,
      },
      "WhatsApp messages received"
    );

    for (const message of messages) {
      // Cache all messages for MCP media download
      cacheMessage(message);
      await handleIncomingMessage(sock, message).catch((error) => {
        logger.error(
          {
            step: "message_handler_unhandled_error",
            messageId: message.key.id,
            err: error,
          },
          "Unhandled error while processing WhatsApp message"
        );
      });
    }
  });
}

async function handleIncomingMessage(sock: WASocket, message: WAMessage): Promise<void> {
  const startedAt = Date.now();
  const messageId = message.key.id;
  const traceId = createTraceId(messageId);
  const remoteJid = message.key.remoteJid;
  const chatType = getChatType(remoteJid);

  logger.info(
    {
      step: "message_flow_start",
      traceId,
      messageId,
    },
    "WhatsApp message flow started"
  );

  try {
    if (message.key.fromMe) {
      rememberBotMessageId(message.key.id);
      logSkipped(traceId, messageId, startedAt, "from_me");
      return;
    }

    if (!remoteJid) {
      logSkipped(traceId, messageId, startedAt, "missing_remote_jid");
      return;
    }

    if (!isProcessableChatType(chatType)) {
      logSkipped(traceId, messageId, startedAt, "unsupported_chat_type", {
        chatType,
        remoteJid: maskJid(remoteJid),
      });
      return;
    }

    if (!message.message) {
      logSkipped(traceId, messageId, startedAt, "message_not_decrypted_or_empty", { chatType });
      return;
    }

    const rawText = extractMessageText(message.message);
    if (!rawText) {
      logSkipped(traceId, messageId, startedAt, "missing_text");
      return;
    }

    const trigger = shouldProcessMessage({
      chatType,
      text: rawText,
      message,
      sock,
      prefix: env.WA_COMMAND_PREFIX,
      mode: env.WA_GROUP_TRIGGER_MODE,
      groupAllowAll: env.WA_GROUP_ALLOW_ALL,
      traceId,
      botMessageIds: botSentMessageIds,
    });

    if (!trigger.shouldProcess) {
      logSkipped(traceId, messageId, startedAt, trigger.reason);
      return;
    }

    if (chatType === "group") {
       logger.info(
        {
          step: "group_trigger_matched",
          traceId,
          messageId,
          reason: trigger.reason,
        },
        "WhatsApp group trigger matched"
      );
    }

    const text = trigger.normalizedText.trim();
    if (!text) {
      if (chatType === "group" && (trigger.isMentioned || trigger.isReplyToBot)) {
        await sendWhatsAppReply({
          sock,
          remoteJid,
          reply: "Halo! Ada yang bisa saya bantu?",
          quoted: message,
          traceId,
          messageId,
          chatType,
          rememberBotMessageId,
        });
        return;
      }
      logSkipped(traceId, messageId, startedAt, "empty_text_after_trigger_cleanup");
      return;
    }

    const payload = buildAIChatPayload({
      remoteJid,
      msg: message,
      chatType,
      normalizedText: text,
      triggerReason: trigger.reason,
      isMentioned: trigger.isMentioned,
      hasPrefix: trigger.hasPrefix,
      isReplyToBot: trigger.isReplyToBot,
      traceId,
      messageId,
    });

    logger.info(
      {
        step: "ai_payload_built",
        traceId,
        messageId,
        chatType,
        hasSenderId: Boolean(payload.sender_id),
        senderIdLength: payload.sender_id.length,
        textLength: payload.message.length,
      },
      "AI payload built successfully",
    );

    const { reply } = await sendChatToAI(payload);

    await sendWhatsAppReply({
      sock,
      remoteJid,
      reply,
      quoted: message,
      traceId,
      messageId,
      chatType,
      rememberBotMessageId,
    });

    logger.info(
      {
        step: "message_flow_completed",
        traceId,
        messageId,
        durationMs: Date.now() - startedAt,
        result: "replied",
      },
      "WhatsApp message flow completed"
    );
  } catch (error) {
    logger.error(
      {
        step: "message_flow_failed",
        traceId,
        messageId,
        durationMs: Date.now() - startedAt,
        err: error,
      },
      "WhatsApp message flow failed"
    );

    await sendFallbackReply(sock, remoteJid, chatType, traceId, messageId);
  }
}

function logSkipped(
  traceId: string,
  messageId: string | null | undefined,
  startedAt: number,
  reason: string,
  meta?: Record<string, unknown>
): void {
  logger.info(
    {
      step: "message_flow_skipped",
      traceId,
      messageId,
      durationMs: Date.now() - startedAt,
      reason,
      ...(meta || {}),
    },
    "WhatsApp message flow skipped"
  );
}

async function sendFallbackReply(
  sock: WASocket,
  remoteJid: string | null | undefined,
  chatType: string,
  traceId: string,
  messageId: string | null | undefined
): Promise<void> {
  if (!remoteJid || (chatType !== "private" && chatType !== "group")) return;

  try {
    const sentMessage = await sendTextMessage(sock, remoteJid, "Maaf, AI sedang bermasalah sebentar. Coba ulangi lagi ya.");
    rememberBotMessageId(sentMessage?.key.id);
  } catch (error) {
    logger.error({ step: "fallback_reply_failed", traceId, messageId, err: error }, "Failed to send fallback reply");
  }
}

function rememberBotMessageId(messageId: string | null | undefined): void {
  if (!messageId) return;
  botSentMessageIds.add(messageId);
  if (botSentMessageIds.size > MAX_TRACKED_BOT_MESSAGES) {
    const oldest = botSentMessageIds.values().next().value;
    if (oldest) botSentMessageIds.delete(oldest);
  }
}
