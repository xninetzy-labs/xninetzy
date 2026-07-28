import {
  downloadMediaMessage,
  type WASocket,
  type WAMessage,
} from "@whiskeysockets/baileys";

import { env } from "../config/env";
import { logger } from "../utils/logger";
import { unwrapMessage } from "../whatsapp/message-parser";
import {
  getStoredMedia,
  getStoredMediaContent,
  saveStoredMedia,
  type StoredMedia,
} from "./durable-media";

export { getStoredMedia, getStoredMediaContent, type StoredMedia } from "./durable-media";

function safeFilename(input: string, fallback: string): string {
  const safe = input.replace(/[^a-zA-Z0-9_\-@.]/g, "_").slice(0, 200);
  return safe || fallback;
}

function describeMedia(message: WAMessage, messageId: string) {
  const content = unwrapMessage(message.message);
  const document = content?.documentMessage;
  const image = content?.imageMessage;
  const video = content?.videoMessage;
  const audio = content?.audioMessage;
  const media = document ?? image ?? video ?? audio;
  if (!content || !media) {
    throw new Error("Message does not contain downloadable media");
  }

  const mediaType: StoredMedia["media_type"] = document
    ? "document"
    : image
      ? "image"
      : video
        ? "video"
        : "audio";
  const mimeType =
    document?.mimetype ??
    image?.mimetype ??
    video?.mimetype ??
    audio?.mimetype ??
    "application/octet-stream";
  const originalFilename =
    document?.fileName ??
    (image ? `image_${messageId}.jpg` : undefined) ??
    (video ? `video_${messageId}.mp4` : undefined) ??
    (audio ? `audio_${messageId}.ogg` : undefined) ??
    `media_${messageId}`;
  const declaredSize = Number(
    document?.fileLength ??
    image?.fileLength ??
    video?.fileLength ??
    audio?.fileLength ??
    0,
  );

  return {
    mediaType,
    mimeType,
    filename: safeFilename(originalFilename, `media_${messageId}`),
    declaredSize,
  };
}

export async function persistMediaMessage(
  sock: WASocket,
  message: WAMessage,
  chatId: string,
  messageId: string,
): Promise<StoredMedia> {
  const existing = getStoredMedia(chatId, messageId);
  if (existing) return existing;

  const description = describeMedia(message, messageId);
  if (description.declaredSize > env.WA_MEDIA_MAX_BYTES) {
    throw new Error(
      `Media exceeds size limit (${description.declaredSize} > ${env.WA_MEDIA_MAX_BYTES} bytes)`,
    );
  }

  logger.info(
    {
      step: "wa_media_persist_start",
      messageId,
      mediaType: description.mediaType,
      mimeType: description.mimeType,
    },
    "Persisting WhatsApp media",
  );

  const downloaded = await downloadMediaMessage(
    message,
    "buffer",
    {},
    { logger: logger as any, reuploadRequest: sock.updateMediaMessage },
  );
  if (!Buffer.isBuffer(downloaded)) {
    throw new Error("Media download returned unexpected type");
  }
  if (downloaded.byteLength > env.WA_MEDIA_MAX_BYTES) {
    throw new Error(
      `Downloaded media exceeds size limit (${downloaded.byteLength} > ${env.WA_MEDIA_MAX_BYTES} bytes)`,
    );
  }

  const stored = saveStoredMedia(
    chatId,
    messageId,
    description.filename,
    downloaded,
    { mime_type: description.mimeType, media_type: description.mediaType },
  );
  logger.info(
    {
      step: "wa_media_persist_done",
      messageId,
      mediaType: stored.media_type,
      sizeBytes: stored.size_bytes,
    },
    "WhatsApp media persisted",
  );
  return stored;
}
