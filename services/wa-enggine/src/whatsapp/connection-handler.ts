import { DisconnectReason, type ConnectionState, type WASocket } from "@whiskeysockets/baileys";
import qrcode from "qrcode-terminal";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import { maskJid, maskPhone } from "../utils/observability";
import { getBotIdentity } from "../utils/jid";
import { getDisconnectStatusCode, getErrorMessage, shouldResetAuthState } from "./disconnect-utils";
import { cleanupCurrentSocket } from "./socket-state";
import { scheduleReconnect, resetReconnectAttempts, getReconnectAttempts } from "./reconnect-manager";
import { isInsidePairingWindow, getPairingWaitRemainingMs, resetPairingState } from "./pairing-manager";
import { clearAuthState } from "./auth";

let isResettingAuthState = false;

export async function handleConnectionUpdate(
  currentSock: WASocket,
  update: Partial<ConnectionState>
): Promise<void> {
  const { connection, lastDisconnect, qr } = update;

  logger.info(
    {
      step: "connection_update",
      connection,
      hasQr: Boolean(qr),
      hasPairingCode: Boolean((update as { pairingCode?: string }).pairingCode),
    },
    "WhatsApp connection update received"
  );

  if (qr) {
    if (env.WA_LOGIN_MODE === "qr") {
      logger.info(
        {
          step: "qr_generated",
          loginMode: env.WA_LOGIN_MODE,
        },
        "QR generated. Scan it from WhatsApp Linked Devices."
      );
      qrcode.generate(qr, { small: true });
    }
  }

  if (connection === "connecting") {
    logger.info({ step: "connection_connecting" }, "WhatsApp connecting");
  }

  if (connection === "open") {
    const attemptsBeforeReset = getReconnectAttempts();
    const botIdentity = getBotIdentity(currentSock);
    
    resetReconnectAttempts();
    resetPairingState();

    logger.info(
      {
        step: "bot_identity_loaded",
        jid: maskJid(botIdentity.jid),
        rawJid: maskJid(botIdentity.rawJid),
        lid: maskJid(botIdentity.lid),
        numberMasked: maskPhone(botIdentity.number),
      },
      "WhatsApp bot identity loaded"
    );

    logger.info(
      {
        step: "connection_open",
        jid: maskJid(currentSock.user?.id),
        name: currentSock.user?.name,
        loginMode: env.WA_LOGIN_MODE,
        authDir: env.WA_AUTH_DIR,
        reconnectAttempts: attemptsBeforeReset,
      },
      "WhatsApp connected successfully"
    );

    return;
  }

  if (connection !== "close") return;

  const statusCode = getDisconnectStatusCode(lastDisconnect?.error);
  const message = getErrorMessage(lastDisconnect?.error);
  const insidePairingWindow = isInsidePairingWindow();
  
  const shouldResetSession = shouldResetAuthState(statusCode, message) && !insidePairingWindow;

  logger.warn(
    {
      step: "connection_closed",
      statusCode,
      reason: message,
      recoverable: !shouldResetSession,
      insidePairingWindow,
    },
    "WhatsApp connection closed"
  );

  cleanupCurrentSocket(`connection_closed_${statusCode ?? "unknown"}`);

  if (shouldResetSession) {
    await resetAuthStateAndScheduleReconnect(`session_reset_${statusCode ?? "unknown"}`);
    return;
  }

  scheduleReconnect(
    `connection_closed_${statusCode ?? "unknown"}`,
    insidePairingWindow ? env.WA_PAIRING_RECONNECT_DELAY_MS : undefined
  );
}

export async function resetAuthStateAndScheduleReconnect(reason: string): Promise<void> {
  if (isResettingAuthState) return;
  isResettingAuthState = true;

  try {
    logger.warn({ step: "session_reset_start", reason, authDir: env.WA_AUTH_DIR }, "Resetting WhatsApp session");
    cleanupCurrentSocket(`session_reset_${reason}`);
    await clearAuthState();
    resetPairingState();
    resetReconnectAttempts();
    logger.warn({ step: "session_reset_completed", reason }, "WhatsApp session reset completed");
  } catch (error) {
    logger.error({ step: "session_reset_failed", err: error }, "Failed to reset WhatsApp session");
  } finally {
    isResettingAuthState = false;
  }

  scheduleReconnect(reason);
}
