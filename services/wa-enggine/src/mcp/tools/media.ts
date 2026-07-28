import type { WAMessage } from "@whiskeysockets/baileys";
import type { McpTool } from "../types";
import { requireString } from "../validation";
import { getStoredMedia, getStoredMediaContent, persistMediaMessage } from "../media-store";
import { unwrapMessage } from "../../whatsapp/message-parser";

function requireStored(input: Record<string, unknown>) {
  const chatId = requireString(input, "chat_id");
  const messageId = requireString(input, "message_id");
  const stored = getStoredMedia(chatId, messageId);
  if (!stored) {
    throw new Error(
      `Message ${messageId} not found in durable store while WhatsApp is disconnected.`,
    );
  }
  return stored;
}

function readMetadata(
  input: Record<string, unknown>,
  recentMessages?: Map<string, WAMessage>,
) {
  const chatId = requireString(input, "chat_id");
  const messageId = requireString(input, "message_id");
  const stored = getStoredMedia(chatId, messageId);
  if (stored) {
    return {
      has_media: true,
      media_type: stored.media_type,
      filename: stored.filename,
      caption: null,
      mime_type: stored.mime_type,
      size_bytes: stored.size_bytes,
      persisted: true,
    };
  }

  const message = recentMessages?.get(messageId);
  const content = unwrapMessage(message?.message);
  const document = content?.documentMessage;
  const image = content?.imageMessage;
  const video = content?.videoMessage;
  const audio = content?.audioMessage;
  const hasMedia = Boolean(document ?? image ?? video ?? audio);
  const mediaType = document
    ? "document"
    : image
      ? "image"
      : video
        ? "video"
        : audio
          ? "audio"
          : null;
  return {
    has_media: hasMedia,
    media_type: mediaType,
    filename: document?.fileName ?? null,
    caption: document?.caption ?? image?.caption ?? video?.caption ?? null,
    mime_type:
      document?.mimetype ?? image?.mimetype ?? video?.mimetype ?? audio?.mimetype ?? null,
    persisted: false,
  };
}

export const mediaTools: McpTool[] = [
  {
    definition: {
      name: "download_media_message",
      description:
        "Ambil media WhatsApp dari durable store atau download dari message cache bila belum tersimpan.",
      inputSchema: {
        type: "object",
        properties: {
          chat_id: { type: "string", description: "WhatsApp JID chat" },
          message_id: { type: "string", description: "ID pesan yang mengandung media" },
        },
        required: ["chat_id", "message_id"],
      },
    },
    async handler(input, { sock, recentMessages }) {
      const chatId = requireString(input, "chat_id");
      const messageId = requireString(input, "message_id");
      const stored = getStoredMedia(chatId, messageId);
      if (stored) return stored;

      const message = recentMessages?.get(messageId);
      if (!message?.message) {
        throw new Error(
          `Message ${messageId} not found in durable store or cache. Ask the user to resend it.`,
        );
      }
      return persistMediaMessage(sock, message, chatId, messageId);
    },
    async offlineHandler(input) {
      return requireStored(input);
    },
  },
  {
    definition: {
      name: "get_message_metadata",
      description: "Cek metadata attachment dari durable store atau cache.",
      inputSchema: {
        type: "object",
        properties: {
          chat_id: { type: "string" },
          message_id: { type: "string" },
        },
        required: ["chat_id", "message_id"],
      },
    },
    async handler(input, { recentMessages }) {
      return readMetadata(input, recentMessages);
    },
    async offlineHandler(input, { recentMessages }) {
      return readMetadata(input, recentMessages);
    },
  },
  {
    definition: {
      name: "get_media_content",
      description: "Ambil byte media durable sebagai base64 ketika filesystem tidak dibagi dengan AI.",
      inputSchema: {
        type: "object",
        properties: {
          chat_id: { type: "string" },
          message_id: { type: "string" },
        },
        required: ["chat_id", "message_id"],
      },
    },
    async handler(input) {
      const chatId = requireString(input, "chat_id");
      const messageId = requireString(input, "message_id");
      const content = getStoredMediaContent(chatId, messageId);
      if (!content) {
        throw new Error(`Message ${messageId} not found in durable media store.`);
      }
      return content;
    },
    async offlineHandler(input) {
      const chatId = requireString(input, "chat_id");
      const messageId = requireString(input, "message_id");
      const content = getStoredMediaContent(chatId, messageId);
      if (!content) throw new Error(`Message ${messageId} not found in durable media store.`);
      return content;
    },
  },
];
