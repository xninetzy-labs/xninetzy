import type { WAMessage, proto } from "@whiskeysockets/baileys";
import type { ChatType } from "../types/chat";

export function extractMessageText(rawMessage?: proto.IMessage | null): string | null {
  const message = unwrapMessage(rawMessage);
  if (!message) return null;
  if (message.protocolMessage) return null;

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

export function getMessageKinds(rawMessage?: proto.IMessage | null): string[] {
  const message = unwrapMessage(rawMessage);
  if (!message) return ["empty"];

  return Object.entries(message)
    .filter(([, value]) => value !== null && value !== undefined)
    .map(([key]) => key);
}

export function getChatType(remoteJid?: string | null): ChatType {
  if (!remoteJid) return "unknown";
  if (remoteJid === "status@broadcast") return "status" as any;
  if (remoteJid.endsWith("@broadcast")) return "broadcast" as any;
  if (remoteJid.endsWith("@g.us")) return "group";
  if (remoteJid.endsWith("@s.whatsapp.net")) return "private";
  if (remoteJid.endsWith("@lid")) return "private";
  return "unknown";
}

export function unwrapMessage(content: proto.IMessage | null | undefined): proto.IMessage | null {
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
