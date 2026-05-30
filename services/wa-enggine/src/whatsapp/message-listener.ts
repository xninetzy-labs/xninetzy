import type { WASocket, WAMessage } from "@whiskeysockets/baileys";

import { sendChatToAI } from "../ai/ai-client";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import {
  buildChatPayload,
  extractMessageText,
  getChatType,
  getMessageKind,
  getMessageKinds,
  getSenderId,
  getSenderName,
  isSupportedChatType,
  shouldProcessMessage,
  type DetectedChatType,
} from "./message-parser";
import { sendTextMessage } from "./message-sender";
import { createTraceId, maskJid, safePreview } from "../utils/observability";

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
  const groupChat = chatType === "group";
  const privateChat = chatType === "private";

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

    logger.info(
      {
        step: "chat_type_detected",
        traceId,
        messageId,
        remoteJid: maskJid(remoteJid),
        chatType,
        supported: isSupportedChatType(remoteJid),
      },
      "WhatsApp chat type detected"
    );

    if (!isSupportedChatType(remoteJid)) {
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

    logger.info(
      {
        step: "message_received",
        traceId,
        messageId,
        remoteJid: maskJid(remoteJid),
        chatType,
        isGroup: groupChat,
        isPrivate: privateChat,
        fromMe: message.key.fromMe,
        hasMessage: Boolean(message.message),
      },
      "Processing WhatsApp message"
    );

    const messageKind = getMessageKind(message.message);
    const messageKinds = getMessageKinds(message.message);
    const rawText = extractMessageText(message.message);

    logger.info(
      {
        step: "message_text_extracted",
        traceId,
        messageId,
        messageKind,
        messageKinds,
        hasText: Boolean(rawText),
        textLength: rawText?.length ?? 0,
      },
      "WhatsApp message text extraction completed"
    );

    if (!rawText) {
      logSkipped(traceId, messageId, startedAt, "missing_text", { messageKind });
      return;
    }

    logger.debug(
      {
        step: "message_text_preview",
        traceId,
        messageId,
        preview: safePreview(rawText),
      },
      "WhatsApp message text preview"
    );

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

    logger.info(
      {
        step: "trigger_detection",
        traceId,
        messageId,
        chatType,
        isGroup: groupChat,
        isPrivate: privateChat,
        isMentioned: trigger.isMentioned,
        hasPrefix: trigger.hasPrefix,
        isReplyToBot: trigger.isReplyToBot,
        shouldProcess: trigger.shouldProcess,
        reason: trigger.reason,
        normalizedTextLength: trigger.normalizedText.length,
      },
      "WhatsApp trigger detection completed"
    );

    if (groupChat && trigger.shouldProcess) {
      logger.info(
        {
          step: "group_trigger_matched",
          traceId,
          messageId,
          reason: trigger.reason,
          isMentioned: trigger.isMentioned,
          hasPrefix: trigger.hasPrefix,
          isReplyToBot: trigger.isReplyToBot,
        },
        "WhatsApp group trigger matched"
      );
    }

    if (!trigger.shouldProcess) {
      if (groupChat) {
        logger.info(
          {
            step: "group_trigger_skipped",
            traceId,
            messageId,
            reason: trigger.reason,
            isMentioned: trigger.isMentioned,
            hasPrefix: trigger.hasPrefix,
            isReplyToBot: trigger.isReplyToBot,
          },
          "WhatsApp group message skipped because trigger did not match"
        );
      }

      logger.info(
        {
          step: "message_skipped",
          traceId,
          messageId,
          reason: trigger.reason,
        },
        "Skipping message because trigger requirements were not met"
      );
      logSkipped(traceId, messageId, startedAt, trigger.reason);
      return;
    }

    const text = trigger.normalizedText.trim();
    if (!text) {
      if (groupChat && (trigger.isMentioned || trigger.isReplyToBot)) {
        await sendWhatsAppReply({
          sock,
          remoteJid,
          reply: "Halo! Ada yang bisa saya bantu?",
          quoted: message,
          traceId,
          messageId,
          chatType,
        });

        logger.info(
          {
            step: "message_flow_completed",
            traceId,
            messageId,
            durationMs: Date.now() - startedAt,
            result: trigger.isReplyToBot ? "replied_empty_reply_greeting" : "replied_empty_mention_greeting",
          },
          "WhatsApp group trigger greeting sent"
        );
        return;
      }

      logSkipped(traceId, messageId, startedAt, "empty_text_after_trigger_cleanup");
      return;
    }

    const payload = buildChatPayload({
      chatId: remoteJid,
      senderId: getSenderId(message),
      senderName: getSenderName(message),
      message: text,
      chatType: chatType as "private" | "group",
      groupName: undefined,
    });

    const { reply } = await sendChatToAI(payload, { traceId, messageId });

    await sendWhatsAppReply({
      sock,
      remoteJid,
      reply,
      quoted: message,
      traceId,
      messageId,
      chatType,
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
  chatType: DetectedChatType,
  traceId: string,
  messageId: string | null | undefined
): Promise<void> {
  if (!remoteJid || (chatType !== "private" && chatType !== "group")) return;

  try {
    const sentMessage = await sendTextMessage(sock, remoteJid, "Maaf, AI sedang bermasalah sebentar. Coba ulangi lagi ya.");
    rememberBotMessageId(sentMessage?.key.id);
  } catch (error) {
    logger.error(
      {
        step: "fallback_reply_failed",
        traceId,
        messageId,
        remoteJid: maskJid(remoteJid),
        err: error,
      },
      "Failed to send fallback reply"
    );
  }
}

async function sendWhatsAppReply(params: {
  sock: WASocket;
  remoteJid: string;
  reply: string;
  quoted: WAMessage;
  traceId: string;
  messageId: string | null | undefined;
  chatType: DetectedChatType;
}): Promise<void> {
  const { sock, remoteJid, reply, quoted, traceId, messageId, chatType } = params;

  logger.info(
    {
      step: "reply_target_selected",
      traceId,
      messageId,
      chatType,
      targetJid: maskJid(remoteJid),
      participantJid: maskJid(quoted.key.participant),
    },
    "WhatsApp reply target selected"
  );

  logger.info(
    {
      step: "reply_sending",
      traceId,
      messageId,
      remoteJid: maskJid(remoteJid),
      replyLength: reply.length,
    },
    "Sending AI reply to WhatsApp"
  );

  try {
    const sentMessage = await sendTextMessage(sock, remoteJid, reply, { quoted });
    rememberBotMessageId(sentMessage?.key.id);
  } catch (error) {
    logger.warn(
      {
        step: "reply_quoted_failed",
        traceId,
        messageId,
        remoteJid: maskJid(remoteJid),
        err: error,
      },
      "Failed to send quoted reply, retrying without quoted message"
    );

    try {
      const sentMessage = await sendTextMessage(sock, remoteJid, reply);
      rememberBotMessageId(sentMessage?.key.id);
    } catch (sendError) {
      logger.error(
        {
          step: "reply_failed",
          traceId,
          messageId,
          remoteJid: maskJid(remoteJid),
          err: sendError,
        },
        "Failed to send WhatsApp reply"
      );
      throw sendError;
    }
  }

  logger.info(
    {
      step: "reply_sent",
      traceId,
      messageId,
      remoteJid: maskJid(remoteJid),
    },
    "AI reply sent to WhatsApp"
  );
}

function rememberBotMessageId(messageId: string | null | undefined): void {
  if (!messageId) return;

  botSentMessageIds.add(messageId);

  if (botSentMessageIds.size <= MAX_TRACKED_BOT_MESSAGES) return;

  const oldest = botSentMessageIds.values().next().value;
  if (oldest) {
    botSentMessageIds.delete(oldest);
  }
}
