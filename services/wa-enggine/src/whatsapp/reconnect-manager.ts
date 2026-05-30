import { logger } from "../utils/logger";
import { startWhatsAppSocket } from "./socket";
import { isInsidePairingWindow, getPairingWaitRemainingMs } from "./pairing-manager";

let reconnectAttempts = 0;
let reconnectTimer: NodeJS.Timeout | null = null;

export function getReconnectAttempts(): number {
  return reconnectAttempts;
}

export function resetReconnectAttempts(): void {
  reconnectAttempts = 0;
}

export function scheduleReconnect(reason: string, overrideDelayMs?: number): void {
  if (reconnectTimer) {
    logger.warn(
      {
        step: "reconnect_skipped",
        reason: "timer_already_exists",
      },
      "Reconnect already scheduled, skipping duplicate reconnect"
    );
    return;
  }

  const delay = overrideDelayMs ?? Math.min(30_000, 2_000 * Math.max(1, reconnectAttempts + 1));
  reconnectAttempts += 1;

  logger.warn(
    {
      step: "reconnect_scheduled",
      reason,
      reconnectAttempts,
      delayMs: delay,
      insidePairingWindow: isInsidePairingWindow(),
      waitRemainingMs: getPairingWaitRemainingMs(),
    },
    "WhatsApp reconnect scheduled"
  );

  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    logger.info(
      {
        step: "reconnect_starting",
        reconnectAttempts,
        insidePairingWindow: isInsidePairingWindow(),
        waitRemainingMs: getPairingWaitRemainingMs(),
      },
      "Starting WhatsApp reconnect"
    );
    startWhatsAppSocket().catch((error) => {
      logger.error({ step: "reconnect_failed", err: error }, "Reconnect failed");
      scheduleReconnect("reconnect_failed");
    });
  }, delay);
}
