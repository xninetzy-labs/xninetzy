import type { WASocket, WAMessage } from "@whiskeysockets/baileys";
import { sendChatToAI } from "../ai/ai-client";
import { buildAIChatPayload, resolveSenderId } from "../ai/ai-payload";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import {
  extractMessageText,
  getChatType,
  getMessageContextInfo,
  getMediaType,
  resolveCaptchaReply,
  resolveGradeTokenReply,
  type MediaKind,
} from "./message-parser";
import { shouldProcessMessage } from "./trigger";
import { sendWhatsAppReply } from "./reply-context";
import { sendTextMessage } from "./message-sender";
import { createTraceId, maskJid } from "../utils/observability";
import { isProcessableChatType } from "../types/chat";
import {
  cacheMessage,
  getCachedMessage,
  resolveActiveCaptchaCommand,
} from "./socket-state";
import { persistMediaMessage } from "../mcp/media-store";
import { runInChatQueue } from "./chat-queue";
import { resolveCanonicalJid } from "./jid-resolver";
import {
  claimMessage,
  markMessageCompleted,
  markMessageFailed,
  markReplyReady,
} from "./message-processing-store";

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

    const jobs = messages.map((message) => {
      // Cache all messages for MCP media download
      cacheMessage(message);
      const chatKey = message.key.remoteJid || message.key.participant || message.key.id || "unknown";
      return runInChatQueue(chatKey, () => handleIncomingMessage(sock, message)).catch((error) => {
        logger.error(
          {
            step: "message_handler_unhandled_error",
            messageId: message.key.id,
            err: error,
          },
          "Unhandled error while processing WhatsApp message"
        );
      });
    });
    await Promise.all(jobs);
  });
}

async function handleIncomingMessage(sock: WASocket, message: WAMessage): Promise<void> {
  const startedAt = Date.now();
  const messageId = message.key.id;
  const traceId = createTraceId(messageId);
  const remoteJid = message.key.remoteJid;
  const chatType = getChatType(remoteJid);
  let processingClaimed = false;
  let replyPrepared = false;

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

    if (!messageId) {
      logSkipped(traceId, messageId, startedAt, "missing_message_id");
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
    const mediaType = getMediaType(message.message);

    // Caption-less media must still reach the AI: skip only when there is
    // neither text nor media. Otherwise synthesize a placeholder caption so the
    // trigger/payload pipeline treats it like a normal message (the real media
    // metadata travels in the payload for the AI to download + parse).
    if (!rawText && !mediaType) {
      logSkipped(traceId, messageId, startedAt, "missing_text");
      return;
    }

    const senderId = await resolveCanonicalJid(
      sock,
      resolveSenderId({ remoteJid, msg: message, chatType }),
    );
    const contextInfo = getMessageContextInfo(message.message);
    const cachedQuotedMessage = getCachedMessage(contextInfo?.stanzaId)?.message;
    const captchaBoundText = resolveCaptchaReply(
      rawText ?? syntheticMediaText(mediaType),
      message.message,
      cachedQuotedMessage,
    );
    const replyBoundText = resolveGradeTokenReply(
      captchaBoundText,
      message.message,
      cachedQuotedMessage,
    );
    const effectiveText = resolveActiveCaptchaCommand(replyBoundText, senderId)
      ?? replyBoundText;

    if (mediaType) {
      logger.info(
        {
          step: "wa_media_detected",
          traceId,
          messageId,
          chatType,
          mediaType,
          hasCaption: Boolean(rawText),
        },
        "WhatsApp media detected"
      );
    }

    const trigger = shouldProcessMessage({
      chatType,
      text: effectiveText,
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

    const claim = claimMessage(remoteJid, messageId);
    if (claim.action === "duplicate") {
      logSkipped(traceId, messageId, startedAt, "duplicate_or_leased", {
        processingStatus: claim.record.status,
        attempts: claim.record.attempts,
      });
      return;
    }
    processingClaimed = true;

    if (claim.action === "resume_reply") {
      replyPrepared = true;
      const outboundMessageId = await sendWhatsAppReply({
        sock,
        remoteJid,
        reply: claim.reply,
        quoted: message,
        traceId,
        messageId,
        chatType,
        rememberBotMessageId,
      });
      markMessageCompleted(remoteJid, messageId, outboundMessageId);
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
        const greeting = "Halo! Ada yang bisa saya bantu?";
        markReplyReady(remoteJid, messageId, greeting);
        replyPrepared = true;
        const outboundMessageId = await sendWhatsAppReply({
          sock,
          remoteJid,
          reply: greeting,
          quoted: message,
          traceId,
          messageId,
          chatType,
          rememberBotMessageId,
        });
        markMessageCompleted(remoteJid, messageId, outboundMessageId);
        return;
      }
      logSkipped(traceId, messageId, startedAt, "empty_text_after_trigger_cleanup");
      return;
    }

    await persistRelevantMedia(sock, message, remoteJid);

    const groupMeta = chatType === "group"
      ? await resolveGroupAdminMetadata(sock, remoteJid, message.key.participant || undefined)
      : { groupName: null, groupAdmins: [], isGroupAdmin: false };
    const payload = buildAIChatPayload({
      remoteJid,
      senderId,
      msg: message,
      chatType,
      normalizedText: text,
      triggerReason: trigger.reason,
      isMentioned: trigger.isMentioned,
      hasPrefix: trigger.hasPrefix,
      isReplyToBot: trigger.isReplyToBot,
      traceId,
      messageId,
      groupName: groupMeta.groupName,
      groupAdmins: groupMeta.groupAdmins,
      isGroupAdmin: groupMeta.isGroupAdmin,
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

    markReplyReady(remoteJid, messageId, reply);
    replyPrepared = true;
    const outboundMessageId = await sendWhatsAppReply({
      sock,
      remoteJid,
      reply,
      quoted: message,
      traceId,
      messageId,
      chatType,
      rememberBotMessageId,
    });
    markMessageCompleted(remoteJid, messageId, outboundMessageId);

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

    if (processingClaimed && remoteJid && messageId && !replyPrepared) {
      try {
        markMessageFailed(remoteJid, messageId, error);
      } catch (storeError) {
        logger.error(
          { step: "message_processing_store_failed", traceId, messageId, err: storeError },
          "Failed to persist message failure state",
        );
      }
    }
    await sendFallbackReply(sock, remoteJid, chatType, traceId, messageId);
  }
}

async function persistRelevantMedia(
  sock: WASocket,
  message: WAMessage,
  remoteJid: string,
): Promise<void> {
  const currentMessageId = message.key.id;
  if (currentMessageId && getMediaType(message.message)) {
    try {
      await persistMediaMessage(sock, message, remoteJid, currentMessageId);
    } catch (error) {
      logger.warn(
        {
          step: "wa_media_persist_failed",
          attachment: "current",
          messageId: currentMessageId,
          err: error,
        },
        "Could not persist current WhatsApp media before AI request",
      );
    }
  }

  const context = getMessageContextInfo(message.message);
  const quotedMessageId = context?.stanzaId;
  if (!quotedMessageId || !context?.quotedMessage || !getMediaType(context.quotedMessage)) {
    return;
  }

  const quotedMessage: WAMessage = {
    key: {
      id: quotedMessageId,
      remoteJid,
      participant: context.participant ?? undefined,
      fromMe: false,
    },
    message: context.quotedMessage,
  };
  try {
    await persistMediaMessage(sock, quotedMessage, remoteJid, quotedMessageId);
  } catch (error) {
    logger.warn(
      {
        step: "wa_media_persist_failed",
        attachment: "quoted",
        messageId: quotedMessageId,
        err: error,
      },
      "Could not persist quoted WhatsApp media before AI request",
    );
  }
}

async function resolveGroupAdminMetadata(
  sock: WASocket,
  groupJid: string,
  participantJid?: string,
): Promise<{ groupName: string | null; groupAdmins: string[]; isGroupAdmin: boolean }> {
  try {
    const metadata = await sock.groupMetadata(groupJid);
    const admins = metadata.participants
      .filter((p) => Boolean(p.admin))
      .map((p) => p.id);
    return {
      groupName: metadata.subject || null,
      groupAdmins: admins,
      isGroupAdmin: Boolean(participantJid && admins.includes(participantJid)),
    };
  } catch (error) {
    logger.warn({ step: "group_admin_metadata_failed", groupJid: maskJid(groupJid), err: error }, "Failed to resolve group admin metadata");
    return { groupName: null, groupAdmins: [], isGroupAdmin: false };
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
): Promise<string | null> {
  if (!remoteJid || (chatType !== "private" && chatType !== "group")) return null;

  try {
    const sentMessage = await sendTextMessage(sock, remoteJid, "Maaf, AI sedang bermasalah sebentar. Coba ulangi lagi ya.");
    rememberBotMessageId(sentMessage?.key.id);
    return sentMessage?.key.id ?? null;
  } catch (error) {
    logger.error({ step: "fallback_reply_failed", traceId, messageId, err: error }, "Failed to send fallback reply");
    return null;
  }
}

function syntheticMediaText(kind: MediaKind | null): string {
  switch (kind) {
    case "image":
      return "[image uploaded]";
    case "document":
      return "[document uploaded]";
    case "audio":
      return "[audio uploaded]";
    case "video":
      return "[video uploaded]";
    default:
      return "[media uploaded]";
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
