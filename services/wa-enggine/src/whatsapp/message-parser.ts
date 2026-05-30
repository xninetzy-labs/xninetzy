import type { WAMessage, proto } from "@whiskeysockets/baileys";

import { env } from "../config/env";
import type { ChatPayload, ChatType } from "../types/message";
import { logger } from "../utils/logger";
import { maskJid, maskPhone } from "../utils/observability";

type AnyMessageContent = proto.IMessage | null | undefined;
export type DetectedChatType = ChatType | "broadcast" | "status" | "unknown";
export type GroupTriggerMode = "mention_only" | "prefix_only" | "mention_or_prefix" | "all";

export type BotIdentity = {
  rawJid: string;
  jid: string;
  lid?: string;
  number: string;
  mentionText: string;
};

export function extractTextMessage(message: WAMessage): string | null {
  return extractMessageText(message.message);
}

export function extractMessageText(rawMessage?: proto.IMessage | null): string | null {
  const message = unwrapMessage(rawMessage);
  if (!message) return null;
  if (message.protocolMessage) return null;
  if (message.senderKeyDistributionMessage && getMessageKinds(rawMessage).length === 1) return null;

  const candidates = [
    message.conversation,
    message.extendedTextMessage?.text,
    message.imageMessage?.caption,
    message.videoMessage?.caption,
    message.documentMessage?.caption,
    message.buttonsResponseMessage?.selectedDisplayText,
    message.buttonsResponseMessage?.selectedButtonId,
    message.listResponseMessage?.title,
    message.listResponseMessage?.singleSelectReply?.selectedRowId,
    message.templateButtonReplyMessage?.selectedDisplayText,
    message.templateButtonReplyMessage?.selectedId,
  ];

  const text = candidates.find((value) => typeof value === "string" && value.trim().length > 0);
  return text?.trim() || null;
}

export function getMessageKind(rawMessage?: proto.IMessage | null): string {
  return getPrimaryMessageKind(rawMessage);
}

export function getMessageKinds(rawMessage?: proto.IMessage | null): string[] {
  const message = unwrapMessage(rawMessage);
  if (!message) return ["empty"];

  return Object.entries(message)
    .filter(([, value]) => value !== null && value !== undefined)
    .map(([key]) => key);
}

export function getPrimaryMessageKind(rawMessage?: proto.IMessage | null): string {
  const kinds = getMessageKinds(rawMessage);
  const priority = [
    "conversation",
    "extendedTextMessage",
    "imageMessage",
    "videoMessage",
    "documentMessage",
    "buttonsResponseMessage",
    "listResponseMessage",
    "templateButtonReplyMessage",
  ];

  return priority.find((kind) => kinds.includes(kind)) || kinds[0] || "unknown";
}

export function getChatType(remoteJid?: string | null): DetectedChatType {
  if (!remoteJid) return "unknown";
  if (remoteJid === "status@broadcast") return "status";
  if (remoteJid.endsWith("@broadcast")) return "broadcast";
  if (remoteJid.endsWith("@g.us")) return "group";
  if (remoteJid.endsWith("@s.whatsapp.net")) return "private";
  if (remoteJid.endsWith("@lid")) return "private";
  return "unknown";
}

export function isSupportedChatType(remoteJid?: string | null): boolean {
  const chatType = getChatType(remoteJid);
  return chatType === "private" || chatType === "group";
}

export function isGroupChat(jid: string): boolean {
  return getChatType(jid) === "group";
}

export function isPrivateChat(jid: string): boolean {
  return getChatType(jid) === "private";
}

export function getSenderId(message: WAMessage): string {
  return message.key.participant ?? message.key.remoteJid ?? "unknown";
}

export function getSenderName(message: WAMessage): string {
  return message.pushName ?? getSenderId(message);
}

export function getMentionedJids(message: WAMessage): string[] {
  return getMentionedJidsFromMessage(message.message);
}

export function getMentionedJidsFromMessage(rawMessage?: proto.IMessage | null): string[] {
  const contextInfo = getMessageContextInfo(rawMessage);
  return (contextInfo?.mentionedJid ?? []).filter(Boolean);
}

export function isBotMentioned(mentionedJids: string[], botJid?: string): boolean {
  const normalizedBotJid = normalizeDigits(botJid);
  if (!normalizedBotJid) return false;
  return mentionedJids.some((jid) => isSameWaIdentity(jid, botJid));
}

export function cleanMentionText(text: string, prefix = "!"): string {
  let output = text || "";
  output = output.replace(/@\d{6,20}/g, "");

  if (output.trim().startsWith(prefix)) {
    output = output.trim().slice(prefix.length);
  }

  return output.replace(/\s+/g, " ").trim();
}

export function buildChatPayload(params: {
  chatId: string;
  senderId: string;
  senderName: string;
  message: string;
  chatType: ChatType;
  groupName?: string | null;
}): ChatPayload {
  return {
    chat_id: params.chatId,
    sender_id: params.senderId,
    sender_name: params.senderName,
    message: params.message,
    chat_type: params.chatType,
    group_name: params.groupName ?? null,
  };
}

export function shouldProcessMessage(params: {
  chatType: DetectedChatType;
  text: string;
  message: WAMessage;
  sock?: { user?: { id?: string } };
  prefix: string;
  mode: string;
  groupAllowAll: boolean;
  traceId?: string;
  botMessageIds?: ReadonlySet<string>;
}): {
  shouldProcess: boolean;
  reason: string;
  normalizedText: string;
  isMentioned: boolean;
  hasPrefix: boolean;
  isReplyToBot: boolean;
} {
  const { chatType, text, message, prefix } = params;
  const mode = normalizeGroupTriggerMode(params.mode);

  if (chatType === "private") {
    return {
      shouldProcess: true,
      reason: "private_chat",
      normalizedText: text,
      isMentioned: false,
      hasPrefix: false,
      isReplyToBot: false,
    };
  }

  if (chatType !== "group") {
    return {
      shouldProcess: false,
      reason: "unsupported_chat_type",
      normalizedText: text,
      isMentioned: false,
      hasPrefix: false,
      isReplyToBot: false,
    };
  }

  const trimmedText = text.trim();
  const hasPrefix = Boolean(prefix) && trimmedText.startsWith(prefix);
  const mentionResult = detectBotMention({
    message,
    text,
    sock: params.sock,
    traceId: params.traceId,
  });
  const isMentioned = mentionResult.isMentioned;
  const replyResult = detectReplyToBot({
    message,
    sock: params.sock,
    botMessageIds: params.botMessageIds,
    traceId: params.traceId,
  });
  const isReplyToBot = replyResult.isReplyToBot;
  const hasDirectBotTrigger = isMentioned || isReplyToBot;

  if (params.groupAllowAll || mode === "all") {
    return {
      shouldProcess: true,
      reason: "group_all_enabled",
      normalizedText: cleanMentionText(text, prefix),
      isMentioned,
      hasPrefix,
      isReplyToBot,
    };
  }

  if (mode === "mention_only") {
    if (!hasDirectBotTrigger) {
      return {
        shouldProcess: false,
        reason: "group_message_without_mention",
        normalizedText: text.trim(),
        isMentioned,
        hasPrefix,
        isReplyToBot,
      };
    }

    return {
      shouldProcess: true,
      reason: isMentioned ? "bot_mentioned" : "bot_message_replied",
      normalizedText: cleanMentionText(text, prefix),
      isMentioned,
      hasPrefix,
      isReplyToBot,
    };
  }

  if (mode === "prefix_only") {
    if (!hasPrefix) {
      return {
        shouldProcess: false,
        reason: "group_message_without_prefix",
        normalizedText: text.trim(),
        isMentioned,
        hasPrefix,
        isReplyToBot,
      };
    }

    return {
      shouldProcess: true,
      reason: "prefix_detected",
      normalizedText: trimmedText.slice(prefix.length).trim(),
      isMentioned,
      hasPrefix,
      isReplyToBot,
    };
  }

  if (hasDirectBotTrigger || hasPrefix) {
    const withoutPrefix = hasPrefix ? trimmedText.slice(prefix.length).trim() : text;
    return {
      shouldProcess: true,
      reason: isMentioned ? "bot_mentioned" : isReplyToBot ? "bot_message_replied" : "prefix_detected",
      normalizedText: cleanMentionText(withoutPrefix, prefix),
      isMentioned,
      hasPrefix,
      isReplyToBot,
    };
  }

  return {
    shouldProcess: false,
    reason: "group_message_without_trigger",
    normalizedText: text,
    isMentioned,
    hasPrefix,
    isReplyToBot,
  };
}

export function unwrapMessage(content: AnyMessageContent): proto.IMessage | null {
  if (!content) return null;

  if (content.ephemeralMessage?.message) {
    return unwrapMessage(content.ephemeralMessage.message);
  }

  if (content.viewOnceMessage?.message) {
    return unwrapMessage(content.viewOnceMessage.message);
  }

  if (content.viewOnceMessageV2?.message) {
    return unwrapMessage(content.viewOnceMessageV2.message);
  }

  if (content.documentWithCaptionMessage?.message) {
    return unwrapMessage(content.documentWithCaptionMessage.message);
  }

  return content;
}

function normalizeGroupTriggerMode(mode: string): GroupTriggerMode {
  if (mode === "mention_only" || mode === "prefix_only" || mode === "mention_or_prefix" || mode === "all") {
    return mode;
  }

  return "mention_or_prefix";
}

export function normalizeDigits(value?: string | null): string {
  if (!value) return "";
  return value.replace(/\D/g, "");
}

export function stripDeviceSuffix(jid?: string | null): string {
  if (!jid) return "";
  const [user, server] = jid.split("@");
  const cleanUser = user.split(":")[0];
  return server ? `${cleanUser}@${server}` : cleanUser;
}

export function getJidNumber(jid?: string | null): string {
  if (!jid) return "";
  const user = jid.split("@")[0]?.split(":")[0] || "";
  return normalizeDigits(user);
}

export function isSameWaIdentity(a?: string | null, b?: string | null): boolean {
  const numA = getJidNumber(a);
  const numB = getJidNumber(b);

  if (!numA || !numB) return false;
  if (numA === numB) return true;

  if (numA.length >= 8 && numB.length >= 8) {
    return numA.endsWith(numB.slice(-8)) || numB.endsWith(numA.slice(-8));
  }

  return false;
}

export function getBotIdentity(sock?: { user?: { id?: string; lid?: string } }): BotIdentity {
  const rawJid = sock?.user?.id || "";
  const rawLid = sock?.user?.lid || "";
  const jid = stripDeviceSuffix(rawJid);
  const lid = rawLid ? stripDeviceSuffix(rawLid) : undefined;
  const number = getJidNumber(rawJid);

  return {
    rawJid,
    jid,
    lid,
    number,
    mentionText: number ? `@${number}` : "",
  };
}

export function getMessageContextInfo(rawMessage?: proto.IMessage | null): proto.IContextInfo | null {
  const message = unwrapMessage(rawMessage);
  if (!message) return null;

  return (
    message.extendedTextMessage?.contextInfo ||
    message.imageMessage?.contextInfo ||
    message.videoMessage?.contextInfo ||
    message.documentMessage?.contextInfo ||
    message.buttonsResponseMessage?.contextInfo ||
    message.listResponseMessage?.contextInfo ||
    message.templateButtonReplyMessage?.contextInfo ||
    null
  );
}

function textMentionsBot(text: string, botNumber: string): boolean {
  const cleanBot = normalizeDigits(botNumber);
  if (!text || !cleanBot) return false;

  const mentionTokens = text.match(/@\d{6,20}/g) || [];
  return mentionTokens.some((token) => {
    const tokenDigits = normalizeDigits(token);
    return (
      tokenDigits === cleanBot ||
      tokenDigits.endsWith(cleanBot.slice(-8)) ||
      cleanBot.endsWith(tokenDigits.slice(-8))
    );
  });
}

function detectBotMention(params: {
  message: WAMessage;
  text: string;
  sock?: { user?: { id?: string; lid?: string } };
  traceId?: string;
}): { isMentioned: boolean; mentionedJids: string[]; mentionedByContext: boolean; mentionedByText: boolean } {
  const { message, text, sock } = params;
  const botIdentity = getBotIdentity(sock);
  const mentionedJids = getMentionedJidsFromMessage(message.message);
  const contextInfo = getMessageContextInfo(message.message);
  const possibleBotJids = [
    botIdentity.rawJid,
    botIdentity.jid,
    botIdentity.lid || "",
    botIdentity.number ? `${botIdentity.number}@s.whatsapp.net` : "",
    botIdentity.number ? `${botIdentity.number}@lid` : "",
  ].filter(Boolean);

  const mentionedByContext =
    mentionedJids.some((jid) => possibleBotJids.some((botJid) => isSameWaIdentity(jid, botJid))) ||
    possibleBotJids.some((botJid) => isSameWaIdentity(contextInfo?.participant, botJid));
  const mentionedByText = textMentionsBot(text, botIdentity.number);
  const mentionedByAnyContext =
    env.WA_GROUP_TREAT_ANY_MENTION_AS_BOT && !mentionedByContext && !mentionedByText && mentionedJids.length > 0;

  logger.info(
    {
      step: "mentioned_jids_detected",
      traceId: params.traceId,
      messageId: message.key.id,
      mentionedCount: mentionedJids.length,
      mentionedJids: mentionedJids.map(maskJid),
      participant: maskJid(contextInfo?.participant),
      botJid: maskJid(botIdentity.jid),
      botRawJid: maskJid(botIdentity.rawJid),
      botLid: maskJid(botIdentity.lid),
      botNumber: maskPhone(botIdentity.number),
      mentionedByContext,
      mentionedByText,
      mentionedByAnyContext,
    },
    "WhatsApp group mention detection completed"
  );

  if (mentionedByAnyContext) {
    logger.warn(
      {
        step: "mention_lid_fallback_matched",
        traceId: params.traceId,
        messageId: message.key.id,
        mentionedJids: mentionedJids.map(maskJid),
      },
      "WhatsApp group mention matched by LID fallback because bot phone JID could not be mapped to mentioned LID"
    );
  }

  if (mentionedByText) {
    logger.info(
      {
        step: "mention_text_detected",
        traceId: params.traceId,
        messageId: message.key.id,
        botNumber: maskPhone(botIdentity.number),
      },
      "WhatsApp group mention detected from message text"
    );
  }

  return {
    isMentioned: mentionedByContext || mentionedByText || mentionedByAnyContext,
    mentionedJids,
    mentionedByContext,
    mentionedByText,
  };
}

function detectReplyToBot(params: {
  message: WAMessage;
  sock?: { user?: { id?: string; lid?: string } };
  botMessageIds?: ReadonlySet<string>;
  traceId?: string;
}): { isReplyToBot: boolean; quotedMessageId?: string; repliedByContext: boolean; repliedByKnownMessageId: boolean } {
  const contextInfo = getMessageContextInfo(params.message.message);
  const quotedMessageId = contextInfo?.stanzaId || "";
  const quotedParticipant = contextInfo?.participant || "";
  const botIdentity = getBotIdentity(params.sock);
  const possibleBotJids = [
    botIdentity.rawJid,
    botIdentity.jid,
    botIdentity.lid || "",
    botIdentity.number ? `${botIdentity.number}@s.whatsapp.net` : "",
    botIdentity.number ? `${botIdentity.number}@lid` : "",
  ].filter(Boolean);

  const repliedByContext = Boolean(
    quotedMessageId && quotedParticipant && possibleBotJids.some((botJid) => isSameWaIdentity(quotedParticipant, botJid))
  );
  const repliedByKnownMessageId = Boolean(quotedMessageId && params.botMessageIds?.has(quotedMessageId));
  const isReplyToBot = repliedByContext || repliedByKnownMessageId;

  if (quotedMessageId || quotedParticipant) {
    logger.info(
      {
        step: "reply_context_detected",
        traceId: params.traceId,
        messageId: params.message.key.id,
        quotedMessageId,
        quotedParticipant: maskJid(quotedParticipant),
        repliedByContext,
        repliedByKnownMessageId,
        isReplyToBot,
      },
      "WhatsApp replied message context detected"
    );
  }

  return {
    isReplyToBot,
    quotedMessageId,
    repliedByContext,
    repliedByKnownMessageId,
  };
}
