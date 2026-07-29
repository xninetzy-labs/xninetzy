import type { WASocket, WAMessage } from "@whiskeysockets/baileys";
import { logger } from "../utils/logger";
import { isSameWaIdentity } from "../utils/jid";

let currentSocket: WASocket | null = null;
export type WhatsAppConnectionStatus = "disconnected" | "connecting" | "open";
let connectionStatus: WhatsAppConnectionStatus = "disconnected";

// Shared recent message cache for MCP media download
const MAX_CACHED_MESSAGES = 500;
const recentMessageCache = new Map<string, WAMessage>();
let activeCaptchaChallenge: {
  challengeId: string;
  targetJid: string;
  expiresAt: number;
} | null = null;

export function cacheMessage(msg: WAMessage): void {
  const id = msg.key.id;
  if (!id) return;
  recentMessageCache.set(id, msg);
  if (recentMessageCache.size > MAX_CACHED_MESSAGES) {
    const oldest = recentMessageCache.keys().next().value;
    if (oldest) recentMessageCache.delete(oldest);
  }
}

export function getRecentMessages(): Map<string, WAMessage> {
  return recentMessageCache;
}

export function getCachedMessage(messageId?: string | null): WAMessage | null {
  if (!messageId) return null;
  return recentMessageCache.get(messageId) ?? null;
}

export function rememberCaptchaChallenge(
  targetJid: string,
  caption: string,
): void {
  const challengeId = caption.match(
    /\/captcha\s+([A-Za-z0-9_-]+)\s+JAWABAN/i,
  )?.[1];
  if (!challengeId) return;
  const rawExpiry = caption.match(/Berlaku sampai:\s*([^\n]+)/i)?.[1]?.trim();
  const parsedExpiry = rawExpiry ? Date.parse(rawExpiry) : Number.NaN;
  activeCaptchaChallenge = {
    challengeId,
    targetJid,
    expiresAt: Number.isFinite(parsedExpiry) ? parsedExpiry : Date.now() + 180_000,
  };
}

export function resolveActiveCaptchaCommand(
  text: string,
  senderJid: string,
  now: number = Date.now(),
): string | null {
  if (!activeCaptchaChallenge) return null;
  if (activeCaptchaChallenge.expiresAt <= now) {
    activeCaptchaChallenge = null;
    return null;
  }
  if (!isSameWaIdentity(senderJid, activeCaptchaChallenge.targetJid)) return null;
  const answer = text.trim();
  if (!/^[A-Za-z0-9+*/=_-]{1,32}$/.test(answer)) return null;
  return `/captcha ${activeCaptchaChallenge.challengeId} ${answer}`;
}

export function clearActiveCaptchaChallenge(): void {
  activeCaptchaChallenge = null;
}

export function getCurrentSocket(): WASocket | null {
  return currentSocket;
}

export function setCurrentSocket(sock: WASocket | null): void {
  currentSocket = sock;
  if (!sock) connectionStatus = "disconnected";
}

export function getConnectionStatus(): WhatsAppConnectionStatus {
  return connectionStatus;
}

export function setConnectionStatus(status: WhatsAppConnectionStatus): void {
  connectionStatus = status;
}

export function isSocketReady(): boolean {
  return Boolean(currentSocket) && connectionStatus === "open";
}

export function cleanupCurrentSocket(reason: string): void {
  if (!currentSocket) return;

  logger.warn(
    {
      step: "socket_cleanup",
      reason,
      hasSocket: true,
    },
    "Cleaning up previous WhatsApp socket before creating a new one"
  );

  const oldSock = currentSocket;
  currentSocket = null;
  connectionStatus = "disconnected";

  try {
    oldSock.ev.removeAllListeners("connection.update");
    oldSock.ev.removeAllListeners("creds.update");
    oldSock.ev.removeAllListeners("messages.upsert");
    oldSock.end(new Error(reason));
  } catch (error) {
    logger.warn({ step: "socket_cleanup_failed", err: error, reason }, "Failed to cleanup old WhatsApp socket");
  }
}
