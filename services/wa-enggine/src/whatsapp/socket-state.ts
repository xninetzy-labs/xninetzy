import type { WASocket } from "@whiskeysockets/baileys";
import { logger } from "../utils/logger";

let currentSocket: WASocket | null = null;

export function getCurrentSocket(): WASocket | null {
  return currentSocket;
}

export function setCurrentSocket(sock: WASocket | null): void {
  currentSocket = sock;
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

  try {
    oldSock.ev.removeAllListeners("connection.update");
    oldSock.ev.removeAllListeners("creds.update");
    oldSock.ev.removeAllListeners("messages.upsert");
    oldSock.end(new Error(reason));
  } catch (error) {
    logger.warn({ step: "socket_cleanup_failed", err: error, reason }, "Failed to cleanup old WhatsApp socket");
  }
}
