import type { WAMessage } from "@whiskeysockets/baileys";
import type { AIChatPayload } from "../types/ai";
import type { ChatType } from "../types/chat";

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
  } = params;

  const senderId = resolveSenderId({
    remoteJid,
    msg,
    chatType,
  });

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
      triggerReason,
      isMentioned,
      hasPrefix,
      isReplyToBot: Boolean(isReplyToBot),
    },
  };
}
