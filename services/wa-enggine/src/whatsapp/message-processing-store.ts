import fs from "node:fs";
import path from "node:path";

import { env } from "../config/env";

export type ProcessingStatus = "processing" | "reply_ready" | "completed" | "failed";

export type MessageProcessingRecord = {
  chat_id: string;
  message_id: string;
  status: ProcessingStatus;
  attempts: number;
  reply?: string;
  outbound_message_id?: string;
  last_error?: string;
  lease_expires_at: number;
  created_at: number;
  updated_at: number;
};

type ProcessingManifest = {
  version: 1;
  records: Record<string, MessageProcessingRecord>;
};

export type ClaimResult =
  | { action: "process"; record: MessageProcessingRecord }
  | { action: "resume_reply"; record: MessageProcessingRecord; reply: string }
  | { action: "duplicate"; record: MessageProcessingRecord };

function storePath(): string {
  return path.resolve(env.WA_PROCESSING_DIR, "message-processing.json");
}

function recordKey(chatId: string, messageId: string): string {
  return `${chatId}\u0000${messageId}`;
}

function emptyManifest(): ProcessingManifest {
  return { version: 1, records: {} };
}

function loadManifest(): ProcessingManifest {
  try {
    const parsed = JSON.parse(fs.readFileSync(storePath(), "utf8")) as ProcessingManifest;
    if (parsed.version !== 1 || !parsed.records || typeof parsed.records !== "object") {
      throw new Error("Invalid message-processing manifest");
    }
    return parsed;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return emptyManifest();
    throw error;
  }
}

function saveManifest(manifest: ProcessingManifest): void {
  const target = storePath();
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const temporary = `${target}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(manifest, null, 2), { mode: 0o600 });
  fs.renameSync(temporary, target);
}

function prune(manifest: ProcessingManifest): void {
  const limit = Math.max(100, env.WA_MESSAGE_RETENTION);
  const entries = Object.entries(manifest.records);
  if (entries.length <= limit) return;

  const active = entries.filter(([, record]) =>
    record.status === "processing" || record.status === "reply_ready"
  );
  const terminal = entries
    .filter(([, record]) => record.status === "completed" || record.status === "failed")
    .sort((a, b) => b[1].updated_at - a[1].updated_at);
  const keep = new Set([
    ...active.map(([key]) => key),
    ...terminal.slice(0, Math.max(0, limit - active.length)).map(([key]) => key),
  ]);
  for (const key of Object.keys(manifest.records)) {
    if (!keep.has(key)) delete manifest.records[key];
  }
}

export function claimMessage(
  chatId: string,
  messageId: string,
  now: number = Date.now(),
): ClaimResult {
  const manifest = loadManifest();
  const key = recordKey(chatId, messageId);
  const existing = manifest.records[key];

  if (existing?.status === "completed") {
    return { action: "duplicate", record: existing };
  }
  if (existing?.status === "reply_ready" && existing.reply) {
    return { action: "resume_reply", record: existing, reply: existing.reply };
  }
  if (existing && existing.lease_expires_at > now) {
    return { action: "duplicate", record: existing };
  }

  const record: MessageProcessingRecord = {
    chat_id: chatId,
    message_id: messageId,
    status: "processing",
    attempts: (existing?.attempts ?? 0) + 1,
    lease_expires_at: now + env.WA_MESSAGE_LEASE_MS,
    created_at: existing?.created_at ?? now,
    updated_at: now,
  };
  manifest.records[key] = record;
  prune(manifest);
  saveManifest(manifest);
  return { action: "process", record };
}

export function markReplyReady(
  chatId: string,
  messageId: string,
  reply: string,
  now: number = Date.now(),
): void {
  updateRecord(chatId, messageId, now, (record) => ({
    ...record,
    status: "reply_ready",
    reply,
    lease_expires_at: 0,
    updated_at: now,
  }));
}

export function markMessageCompleted(
  chatId: string,
  messageId: string,
  outboundMessageId?: string | null,
  now: number = Date.now(),
): void {
  updateRecord(chatId, messageId, now, (record) => ({
    ...record,
    status: "completed",
    outbound_message_id: outboundMessageId || record.outbound_message_id,
    lease_expires_at: 0,
    updated_at: now,
  }));
}

export function markMessageFailed(
  chatId: string,
  messageId: string,
  error: unknown,
  now: number = Date.now(),
): void {
  updateRecord(chatId, messageId, now, (record) => ({
    ...record,
    status: "failed",
    last_error: String(error).slice(0, 1_000),
    lease_expires_at: now + env.WA_MESSAGE_RETRY_DELAY_MS,
    updated_at: now,
  }));
}

function updateRecord(
  chatId: string,
  messageId: string,
  now: number,
  update: (record: MessageProcessingRecord) => MessageProcessingRecord,
): void {
  const manifest = loadManifest();
  const key = recordKey(chatId, messageId);
  const existing = manifest.records[key] ?? {
    chat_id: chatId,
    message_id: messageId,
    status: "processing" as const,
    attempts: 1,
    lease_expires_at: now,
    created_at: now,
    updated_at: now,
  };
  manifest.records[key] = update(existing);
  prune(manifest);
  saveManifest(manifest);
}

export function getMessageRecord(
  chatId: string,
  messageId: string,
): MessageProcessingRecord | null {
  return loadManifest().records[recordKey(chatId, messageId)] ?? null;
}
