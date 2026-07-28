import type { WASocket, WAMessage } from "@whiskeysockets/baileys";
import { logger } from "../utils/logger";

let currentSocket: WASocket | null = null;
export type WhatsAppConnectionStatus = "disconnected" | "connecting" | "open";
let connectionStatus: WhatsAppConnectionStatus = "disconnected";

// Shared recent message cache for MCP media download
const MAX_CACHED_MESSAGES = 500;
const recentMessageCache = new Map<string, WAMessage>();

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
