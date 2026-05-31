import type { WAMessage, proto } from "@whiskeysockets/baileys";
import { getBotIdentity, isSameWaIdentity, normalizeDigits } from "../utils/jid";
import { getMessageContextInfo } from "./message-parser";

export type GroupTriggerMode = "mention_only" | "prefix_only" | "mention_or_prefix" | "all";

export function shouldProcessMessage(params: {
  chatType: "private" | "group";
  text: string;
  message: WAMessage;
  sock?: { user?: { id?: string; lid?: string } };
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

function normalizeGroupTriggerMode(mode: string): GroupTriggerMode {
  if (mode === "mention_only" || mode === "prefix_only" || mode === "mention_or_prefix" || mode === "all") {
    return mode;
  }
  return "mention_or_prefix";
}

export function cleanMentionText(text: string, prefix = "!"): string {
  let output = text || "";
  output = output.replace(/@\d{6,20}/g, "");

  if (output.trim().startsWith(prefix)) {
    output = output.trim().slice(prefix.length);
  }

  return output.replace(/\s+/g, " ").trim();
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
}): { isMentioned: boolean; mentionedJids: string[] } {
  const { message, text, sock } = params;
  const botIdentity = getBotIdentity(sock);
  const contextInfo = getMessageContextInfo(message.message);
  const mentionedJids = (contextInfo?.mentionedJid ?? []).filter(Boolean) as string[];
  
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

  return {
    isMentioned: mentionedByContext || mentionedByText,
    mentionedJids,
  };
}

function detectReplyToBot(params: {
  message: WAMessage;
  sock?: { user?: { id?: string; lid?: string } };
  botMessageIds?: ReadonlySet<string>;
  traceId?: string;
}): { isReplyToBot: boolean } {
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
  
  return {
    isReplyToBot: repliedByContext || repliedByKnownMessageId,
  };
}
