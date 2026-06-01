import type { McpTool } from "../types";
import { requireString } from "../validation";
import * as fs from "node:fs";
import * as path from "node:path";
import * as crypto from "node:crypto";
import { logger } from "../../utils/logger";
import { downloadMediaMessage } from "@whiskeysockets/baileys";

const MEDIA_BASE = process.env.WA_MEDIA_DIR ?? "/app/data/wa-media";

function safeDir(input: string): string {
  return input.replace(/[^a-zA-Z0-9_\-@.]/g, "_").slice(0, 120);
}

function validatePath(resolved: string, base: string): void {
  if (!resolved.startsWith(path.resolve(base))) {
    throw new Error("Path traversal detected");
  }
}

export const mediaTools: McpTool[] = [
  {
    definition: {
      name: "download_media_message",
      description:
        "Download media (dokumen, gambar, video, audio) dari pesan WhatsApp ke disk dan kembalikan path lokal. Dipakai AI service untuk membaca file yang dikirim user.",
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

      // Look up message from recent message cache
      const msg = recentMessages?.get(messageId);
      if (!msg || !msg.message) {
        throw new Error(`Message ${messageId} not found in cache. Media may have expired.`);
      }

      const destDir = path.resolve(MEDIA_BASE, safeDir(chatId), safeDir(messageId));
      validatePath(destDir, MEDIA_BASE);
      fs.mkdirSync(destDir, { recursive: true });

      // Detect media type
      const msgContent = msg.message;
      const docMsg = msgContent.documentMessage;
      const imgMsg = msgContent.imageMessage;
      const videoMsg = msgContent.videoMessage;
      const audioMsg = msgContent.audioMessage;

      const mediaMsg = docMsg ?? imgMsg ?? videoMsg ?? audioMsg;
      if (!mediaMsg) {
        throw new Error("Message does not contain downloadable media");
      }

      const mimetype: string =
        docMsg?.mimetype ??
        imgMsg?.mimetype ??
        videoMsg?.mimetype ??
        audioMsg?.mimetype ??
        "application/octet-stream";

      const originalFilename: string =
        docMsg?.fileName ??
        (imgMsg ? `image_${messageId}.jpg` : undefined) ??
        (videoMsg ? `video_${messageId}.mp4` : undefined) ??
        (audioMsg ? `audio_${messageId}.ogg` : undefined) ??
        `media_${messageId}`;

      const safeFilename = safeDir(originalFilename).slice(0, 200);
      const destPath = path.join(destDir, safeFilename);
      validatePath(destPath, MEDIA_BASE);

      logger.info(
        { step: "mcp_download_media", chatId, messageId, mimetype, safeFilename },
        "Downloading WA media",
      );

      // Download using Baileys helper
      const buffer = await downloadMediaMessage(
        msg,
        "buffer",
        {},
        { logger: logger as any, reuploadRequest: sock.updateMediaMessage },
      );

      if (!Buffer.isBuffer(buffer)) {
        throw new Error("Media download returned unexpected type");
      }

      fs.writeFileSync(destPath, buffer);

      const sha256 = crypto.createHash("sha256").update(buffer).digest("hex");
      const sizeBytes = buffer.byteLength;

      logger.info(
        { step: "mcp_download_media_done", destPath, sizeBytes, sha256 },
        "WA media downloaded",
      );

      return {
        local_path: destPath,
        filename: safeFilename,
        mime_type: mimetype,
        size_bytes: sizeBytes,
        sha256,
      };
    },
  },
  {
    definition: {
      name: "get_message_metadata",
      description: "Cek apakah pesan mengandung media/attachment tanpa mendownload.",
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
      const messageId = requireString(input, "message_id");
      const msg = recentMessages?.get(messageId);
      if (!msg || !msg.message) {
        return { has_media: false, media_type: null, filename: null, caption: null, mime_type: null };
      }

      const m = msg.message;
      const doc = m.documentMessage;
      const img = m.imageMessage;
      const vid = m.videoMessage;
      const aud = m.audioMessage;

      const hasMedia = Boolean(doc ?? img ?? vid ?? aud);
      const mediaType = doc ? "document" : img ? "image" : vid ? "video" : aud ? "audio" : null;

      return {
        has_media: hasMedia,
        media_type: mediaType,
        filename: doc?.fileName ?? null,
        caption: doc?.caption ?? img?.caption ?? vid?.caption ?? null,
        mime_type: doc?.mimetype ?? img?.mimetype ?? vid?.mimetype ?? null,
      };
    },
  },
];
