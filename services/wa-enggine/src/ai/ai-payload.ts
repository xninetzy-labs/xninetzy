import type { WAMessage, proto } from "@whiskeysockets/baileys";
import type { AIChatPayload } from "../types/ai";
import type { ChatType } from "../types/chat";
import {
  getMessageContextInfo,
  extractMessageText,
  unwrapMessage,
} from "../whatsapp/message-parser";

type MediaMeta = {
  hasMedia: true;
  mediaType: "document" | "image" | "video" | "audio";
  filename: string | null;
  mimetype: string | null;
  fileLength: number;
  messageId: string | null;
  caption: string | null;
};

/** Extract media metadata from an (unwrapped) message, or null if it has none. */
function extractMediaMeta(
  rawMessage: proto.IMessage | null | undefined,
  messageId: string | null,
): MediaMeta | null {
  const message = unwrapMessage(rawMessage);
  if (!message) return null;
  const docMsg = message.documentMessage;
  const imgMsg = message.imageMessage;
  const vidMsg = message.videoMessage;
  const audMsg = message.audioMessage;
  if (!(docMsg || imgMsg || vidMsg || audMsg)) return null;

  return {
    hasMedia: true,
    mediaType: docMsg ? "document" : imgMsg ? "image" : vidMsg ? "video" : "audio",
    filename: docMsg?.fileName ?? null,
    mimetype:
      docMsg?.mimetype ?? imgMsg?.mimetype ?? vidMsg?.mimetype ?? audMsg?.mimetype ?? null,
    fileLength: Number(
      docMsg?.fileLength ?? imgMsg?.fileLength ?? vidMsg?.fileLength ?? audMsg?.fileLength ?? 0,
    ),
    messageId,
    caption: docMsg?.caption ?? imgMsg?.caption ?? vidMsg?.caption ?? null,
  };
}

type BuildAIChatPayloadParams = {
  remoteJid: string;
  msg: WAMessage;
  chatType: ChatType;
  normalizedText: string;
  triggerReason: string;
  isMentioned: boolean;
  hasPrefix: boolean;
  isReplyToBot?: boolean;
  traceId: string;
  messageId?: string | null;
  groupName?: string | null;
  groupAdmins?: string[];
  isGroupAdmin?: boolean;
};

export function resolveSenderId(params: {
  remoteJid: string;
  msg: WAMessage;
  chatType: ChatType;
}): string {
  const { remoteJid, msg, chatType } = params;

  if (chatType === "group") {
    return msg.key.participant || remoteJid;
  }

  return msg.key.participant || msg.key.remoteJid || remoteJid;
}

export function resolveSenderName(msg: WAMessage): string {
  return msg.pushName?.trim() || "User";
}

export function buildAIChatPayload(
  params: BuildAIChatPayloadParams,
): AIChatPayload {
  const {
    remoteJid,
    msg,
    chatType,
    normalizedText,
    triggerReason,
    isMentioned,
    hasPrefix,
    isReplyToBot,
    traceId,
    messageId,
    groupName,
    groupAdmins,
    isGroupAdmin,
  } = params;

  const senderId = resolveSenderId({ remoteJid, msg, chatType });
  const contextInfo = getMessageContextInfo(msg.message);
  const quotedMessageText = contextInfo?.quotedMessage ? extractMessageText(contextInfo.quotedMessage) : null;

  // Media on the message itself (document/image/video/audio).
  const media = extractMediaMeta(msg.message, messageId ?? null);

  // Media on a quoted message ("reply to this file and explain it").
  const quotedMediaBase = contextInfo?.quotedMessage
    ? extractMediaMeta(contextInfo.quotedMessage, contextInfo.stanzaId ?? null)
    : null;
  const quotedMedia = quotedMediaBase
    ? { ...quotedMediaBase, participantJid: contextInfo?.participant ?? null }
    : null;

  const mentions = (contextInfo?.mentionedJid ?? []).filter(Boolean) as string[];

  return {
    chat_id: remoteJid,
    sender_id: senderId,
    sender_name: resolveSenderName(msg),
    message: normalizedText,
    chat_type: chatType === "group" ? "group" : "private",
    group_name: chatType === "group" ? groupName ?? null : null,
    metadata: {
      traceId,
      messageId,
      isGroup: chatType === "group",
      chatJid: remoteJid,
      groupJid: chatType === "group" ? remoteJid : undefined,
      participantJid: msg.key.participant || null,
      senderJid: senderId,
      senderName: resolveSenderName(msg),
      isGroupAdmin: Boolean(isGroupAdmin),
      senderIsGroupAdmin: Boolean(isGroupAdmin),
      groupAdmins: groupAdmins ?? [],
      quotedMessageId: contextInfo?.stanzaId || null,
      quotedParticipantJid: contextInfo?.participant || null,
      quotedMessageText,
      triggerReason,
      isMentioned,
      hasPrefix,
      isReplyToBot: Boolean(isReplyToBot),
      mentions,
      media,
      quotedMedia,
    },
  };
}
