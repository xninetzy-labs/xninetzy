import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

import { env } from "../config/env";

const MANIFEST_NAME = "_media.json";

export type StoredMedia = {
  local_path: string;
  filename: string;
  mime_type: string;
  media_type: "document" | "image" | "video" | "audio";
  size_bytes: number;
  sha256: string;
};

export type StoredMediaContent = StoredMedia & {
  content_base64: string;
};

function safeSegment(input: string, fallback: string): string {
  const safe = input.replace(/[^a-zA-Z0-9_\-@.]/g, "_").slice(0, 200);
  return safe || fallback;
}

function mediaDirectory(chatId: string, messageId: string): string {
  return path.resolve(
    env.WA_MEDIA_DIR,
    safeSegment(chatId, "chat"),
    safeSegment(messageId, "message"),
  );
}

function assertInsideMediaBase(candidate: string): void {
  const base = path.resolve(env.WA_MEDIA_DIR);
  const resolved = path.resolve(candidate);
  if (resolved !== base && !resolved.startsWith(`${base}${path.sep}`)) {
    throw new Error("Path traversal detected");
  }
}

function manifestPath(chatId: string, messageId: string): string {
  return path.join(mediaDirectory(chatId, messageId), MANIFEST_NAME);
}

function atomicWrite(target: string, data: Buffer | string): void {
  const temporary = `${target}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(temporary, data);
  fs.renameSync(temporary, target);
}

export function getStoredMedia(chatId: string, messageId: string): StoredMedia | null {
  try {
    const raw = fs.readFileSync(manifestPath(chatId, messageId), "utf8");
    const parsed = JSON.parse(raw) as StoredMedia;
    assertInsideMediaBase(parsed.local_path);
    if (!fs.statSync(parsed.local_path).isFile()) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function getStoredMediaContent(
  chatId: string,
  messageId: string,
): StoredMediaContent | null {
  const stored = getStoredMedia(chatId, messageId);
  if (!stored) return null;
  const buffer = fs.readFileSync(stored.local_path);
  if (buffer.byteLength > env.WA_MEDIA_MAX_BYTES) {
    throw new Error(
      `Stored media exceeds size limit (${buffer.byteLength} > ${env.WA_MEDIA_MAX_BYTES} bytes)`,
    );
  }
  return { ...stored, content_base64: buffer.toString("base64") };
}

export function saveStoredMedia(
  chatId: string,
  messageId: string,
  filename: string,
  buffer: Buffer,
  metadata: Pick<StoredMedia, "mime_type" | "media_type">,
): StoredMedia {
  const directory = mediaDirectory(chatId, messageId);
  assertInsideMediaBase(directory);
  fs.mkdirSync(directory, { recursive: true });
  const safeFilename = safeSegment(filename, `media_${messageId}`);
  const localPath = path.join(directory, safeFilename);
  assertInsideMediaBase(localPath);
  atomicWrite(localPath, buffer);

  const stored: StoredMedia = {
    local_path: localPath,
    filename: safeFilename,
    mime_type: metadata.mime_type,
    media_type: metadata.media_type,
    size_bytes: buffer.byteLength,
    sha256: crypto.createHash("sha256").update(buffer).digest("hex"),
  };
  atomicWrite(manifestPath(chatId, messageId), JSON.stringify(stored, null, 2));
  return stored;
}
