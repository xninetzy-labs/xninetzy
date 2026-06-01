import type { WAMessage } from "@whiskeysockets/baileys";
import type { AIChatPayload } from "../types/ai";
import type { ChatType } from "../types/chat";
import { getMessageContextInfo, extractMessageText } from "../whatsapp/message-parser";

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

  // Media metadata (document/image/video/audio)
  const rawMsg = msg.message;
  const docMsg = rawMsg?.documentMessage;
  const imgMsg = rawMsg?.imageMessage;
  const vidMsg = rawMsg?.videoMessage;
  const audMsg = rawMsg?.audioMessage;
  const hasMedia = Boolean(docMsg ?? imgMsg ?? vidMsg ?? audMsg);
  const media = hasMedia
    ? {
        hasMedia: true,
        mediaType: docMsg ? "document" : imgMsg ? "image" : vidMsg ? "video" : "audio",
        filename: docMsg?.fileName ?? null,
        mimetype: docMsg?.mimetype ?? imgMsg?.mimetype ?? vidMsg?.mimetype ?? null,
        fileLength: Number(docMsg?.fileLength ?? imgMsg?.fileLength ?? vidMsg?.fileLength ?? 0),
        messageId,
        caption: docMsg?.caption ?? imgMsg?.caption ?? vidMsg?.caption ?? null,
      }
    : null;

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
      media,
    },
  };
}
