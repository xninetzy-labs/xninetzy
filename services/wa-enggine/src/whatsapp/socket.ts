import makeWASocket, {
  DisconnectReason,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  type ConnectionState,
  type WASocket,
} from "@whiskeysockets/baileys";
import { Boom } from "@hapi/boom";
import qrcode from "qrcode-terminal";

import { env } from "../config/env";
import { createAuthState, clearAuthState } from "./auth";
import { registerMessageListener } from "./message-listener";
import { getBotIdentity } from "./message-parser";
import { logger } from "../utils/logger";
import { maskJid, maskPhone } from "../utils/observability";

let sock: WASocket | null = null;
let reconnectAttempts = 0;
let reconnectTimer: NodeJS.Timeout | null = null;
let isStarting = false;
let isResettingAuthState = false;
let processHandlersRegistered = false;
let pairingRequested = false;
let isPairingPending = false;
let lastPairingCodeAt = 0;
const baileysLogger = logger.child({ component: "baileys" });

baileysLogger.level = process.env.WA_BAILEYS_LOG_LEVEL ?? "warn";

export async function startWhatsAppSocket(): Promise<void> {
  registerProcessHandlers();

  logger.info(
    {
      step: "start_requested",
      isStarting,
      hasSocket: Boolean(sock),
    },
    "WhatsApp start requested"
  );

  if (isStarting) {
    logger.warn(
      {
        step: "start_skipped",
        reason: "already_starting",
      },
      "WhatsApp start skipped because startup is already running"
    );
    return;
  }

  isStarting = true;

  try {
    cleanupSocket("replace_socket_before_start");

    const { state, saveCreds } = await createAuthState();

    logger.info({ step: "baileys_version_fetching" }, "Fetching latest Baileys version");
    const { version, isLatest } = await fetchLatestBaileysVersion();
    logger.info(
      {
        step: "baileys_version_loaded",
        version,
        isLatest,
      },
      "Baileys version loaded"
    );

    logger.info(
      {
        step: "socket_creating",
        authDir: env.WA_AUTH_DIR,
        baileysVersion: version.join("."),
        registered: state.creds.registered,
        loginMode: env.WA_LOGIN_MODE,
        qrMode: env.WA_LOGIN_MODE === "qr",
        pairingMode: env.WA_LOGIN_MODE === "pairing_code" && !state.creds.registered,
        hasExistingSocket: Boolean(sock),
      },
      "Creating WhatsApp socket"
    );

    const nextSock = makeWASocket({
      auth: {
        creds: state.creds,
        keys: makeCacheableSignalKeyStore(state.keys, baileysLogger),
      },
      version,
      printQRInTerminal: env.WA_LOGIN_MODE === "qr",
      logger: baileysLogger,
      browser: ["Ubuntu", "Chrome", "22.04.4"],
      connectTimeoutMs: env.WA_CONNECT_TIMEOUT_MS,
      defaultQueryTimeoutMs: env.WA_QUERY_TIMEOUT_MS,
      keepAliveIntervalMs: env.WA_KEEP_ALIVE_INTERVAL_MS,
      markOnlineOnConnect: false,
      syncFullHistory: false,
      generateHighQualityLinkPreview: false,
    });

    sock = nextSock;

    logger.info(
      {
        step: "socket_created",
        user: maskJid(nextSock.user?.id),
      },
      "WhatsApp socket created"
    );

    nextSock.ev.on("creds.update", async () => {
      logger.debug({ step: "creds_update_received" }, "WhatsApp credentials update received");
      await saveCreds();
      logger.debug({ step: "creds_saved" }, "WhatsApp credentials saved");
    });
    nextSock.ev.on("connection.update", (update) => {
      void handleConnectionUpdate(nextSock, update);
    });

    registerMessageListener(nextSock);
    await requestPairingCodeIfNeeded(nextSock, state.creds.registered);
  } catch (error) {
    const statusCode = getDisconnectStatusCode(error);
    logger.error({ step: "start_failed", statusCode, err: error }, "Failed to start WhatsApp");

    if (shouldResetAuthState(statusCode, getErrorMessage(error))) {
      await resetAuthStateAndScheduleReconnect(`start_failed_${statusCode ?? "unknown"}`);
      return;
    }

    scheduleReconnect("start_failed");
  } finally {
    isStarting = false;
  }
}

async function handleConnectionUpdate(
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
    } else {
      logger.debug(
        {
          step: "qr_ignored",
          loginMode: env.WA_LOGIN_MODE,
        },
        "QR received but ignored because login mode is pairing_code"
      );
    }
  }

  if (connection === "connecting") {
    logger.info({ step: "connection_connecting" }, "WhatsApp connecting");
  }

  if (connection === "open") {
    const attemptsBeforeReset = reconnectAttempts;
    const botIdentity = getBotIdentity(currentSock);
    reconnectAttempts = 0;
    pairingRequested = false;
    isPairingPending = false;
    lastPairingCodeAt = 0;

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

    if (attemptsBeforeReset > 0) {
      logger.info(
        {
          step: "reconnect_success",
          reconnectAttempts: attemptsBeforeReset,
        },
        "WhatsApp reconnect completed"
      );
    }
    return;
  }

  if (connection !== "close") return;

  const statusCode = getDisconnectStatusCode(lastDisconnect?.error);
  const message = getErrorMessage(lastDisconnect?.error);
  const insidePairingWindow = isInsidePairingWindow();
  const shouldLogout = (statusCode === DisconnectReason.loggedOut || statusCode === 401) && !insidePairingWindow;
  const shouldResetSession = shouldResetAuthState(statusCode, message) && !insidePairingWindow;
  const isRecoverable = !shouldLogout;

  logger.warn(
    {
      step: "connection_closed",
      statusCode,
      reason: message,
      isLoggedOut: shouldLogout,
      recoverable: isRecoverable,
      isPairingPending,
      insidePairingWindow,
    },
    "WhatsApp connection closed"
  );

  if (statusCode === 515) {
    logger.warn(
      {
        step: "connection_restart_required",
        statusCode,
        recoverable: true,
      },
      "WhatsApp stream error 515 detected, reconnect will be scheduled"
    );
  }

  if (statusCode === 408 || message.includes("Timed Out") || message.includes("Request Time-out")) {
    logger.warn(
      {
        step: "connection_timeout",
        statusCode,
        recoverable: true,
      },
      "WhatsApp query timeout detected, reconnect will be scheduled"
    );
  }

  if (statusCode === 428) {
    logger.warn(
      {
        step: "connection_428_recoverable",
        statusCode,
        recoverable: true,
      },
      "WhatsApp connection terminated during pairing/login. Reconnecting without deleting session."
    );
  }

  if (statusCode === 401 && insidePairingWindow) {
    logger.warn(
      {
        step: "connection_401_pairing_pending",
        statusCode,
        recoverable: true,
        waitRemainingMs: getPairingWaitRemainingMs(),
      },
      "WhatsApp returned 401 while pairing is pending. Waiting before resetting session."
    );
  }

  cleanupSocket(`connection_closed_${statusCode ?? "unknown"}`);

  if (shouldResetSession) {
    logger.error(
      {
        step: "session_logged_out",
        statusCode,
        authDir: env.WA_AUTH_DIR,
      },
      "WhatsApp auth/session failed. Removing saved login and starting pairing again."
    );

    await resetAuthStateAndScheduleReconnect(`session_reset_${statusCode ?? "unknown"}`);
    return;
  }

  scheduleReconnect(
    `connection_closed_${statusCode ?? "unknown"}`,
    insidePairingWindow ? env.WA_PAIRING_RECONNECT_DELAY_MS : undefined
  );
}

async function requestPairingCodeIfNeeded(currentSock: WASocket, registered: boolean): Promise<void> {
  if (registered) {
    logger.info(
      {
        step: "pairing_skipped",
        reason: "session_already_registered",
      },
      "Skipping pairing because existing session is registered"
    );
    return;
  }

  logger.info(
    {
      step: "pairing_required",
      loginMode: env.WA_LOGIN_MODE,
      qrMode: env.WA_LOGIN_MODE === "qr",
      pairingMode: env.WA_LOGIN_MODE === "pairing_code",
      hasPhoneNumber: Boolean(env.WA_PHONE_NUMBER),
    },
    "WhatsApp session is not registered, pairing is required"
  );

  if (env.WA_LOGIN_MODE === "qr") {
    logger.info(
      {
        step: "qr_login_required",
        authDir: env.WA_AUTH_DIR,
      },
      "WhatsApp session is not registered. Waiting for QR scan."
    );
    return;
  }

  if (!env.WA_PHONE_NUMBER) return;

  if (isInsidePairingWindow()) {
    logger.warn(
      {
        step: "pairing_code_skipped",
        reason: "pairing_pending",
        waitRemainingMs: getPairingWaitRemainingMs(),
      },
      "Skipping pairing code request because pairing is still pending"
    );
    return;
  }

  if (pairingRequested) return;

  const phoneNumber = env.WA_PHONE_NUMBER.replace(/\D/g, "");
  logger.info(
    {
      step: "pairing_code_requesting",
      phone: maskPhone(env.WA_PHONE_NUMBER),
    },
    "Requesting WhatsApp pairing code"
  );

  logger.info({ step: "pairing_socket_waiting" }, "Waiting for WhatsApp socket before requesting pairing code");
  await currentSock.waitForSocketOpen();

  const code = await currentSock.requestPairingCode(phoneNumber);
  pairingRequested = true;
  isPairingPending = true;
  lastPairingCodeAt = Date.now();

  logger.info(
    {
      step: "pairing_code_generated",
      code,
      pairingWaitMs: env.WA_PAIRING_WAIT_MS,
    },
    "WhatsApp pairing code generated"
  );
}

function scheduleReconnect(reason: string, overrideDelayMs?: number): void {
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
      isPairingPending,
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
        isPairingPending,
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

async function resetAuthStateAndScheduleReconnect(reason: string): Promise<void> {
  if (isResettingAuthState) {
    logger.warn(
      {
        step: "session_reset_skipped",
        reason: "already_resetting",
      },
      "WhatsApp auth reset already running, skipping duplicate reset"
    );
    return;
  }

  isResettingAuthState = true;

  try {
    logger.warn(
      {
        step: "session_reset_start",
        reason,
        authDir: env.WA_AUTH_DIR,
      },
      "Resetting WhatsApp saved login before pairing again"
    );

    cleanupSocket(`session_reset_${reason}`);
    await clearAuthState();
    pairingRequested = false;
    isPairingPending = false;
    lastPairingCodeAt = 0;
    reconnectAttempts = 0;

    logger.warn(
      {
        step: "session_reset_completed",
        reason,
        authDir: env.WA_AUTH_DIR,
      },
      "WhatsApp saved login removed; pairing will be requested again"
    );
  } catch (error) {
    logger.error(
      {
        step: "session_reset_failed",
        reason,
        authDir: env.WA_AUTH_DIR,
        err: error,
      },
      "Failed to reset WhatsApp saved login"
    );
  } finally {
    isResettingAuthState = false;
  }

  scheduleReconnect(reason);
}

function cleanupSocket(reason: string): void {
  if (!sock) return;

  logger.warn(
    {
      step: "socket_cleanup",
      reason,
      hasSocket: Boolean(sock),
    },
    "Cleaning up previous WhatsApp socket before creating a new one"
  );

  const oldSock = sock;
  sock = null;

  try {
    oldSock.ev.removeAllListeners("connection.update");
    oldSock.ev.removeAllListeners("creds.update");
    oldSock.ev.removeAllListeners("messages.upsert");
    oldSock.end(new Error(reason));
  } catch (error) {
    logger.warn({ step: "socket_cleanup_failed", err: error, reason }, "Failed to cleanup old WhatsApp socket");
  }
}

function getDisconnectStatusCode(error: unknown): number | undefined {
  return (
    (error as Boom | undefined)?.output?.statusCode ??
    (error as { data?: { statusCode?: number } } | undefined)?.data?.statusCode ??
    (error as { statusCode?: number } | undefined)?.statusCode
  );
}

function getErrorMessage(error: unknown): string {
  return (error as { message?: string } | undefined)?.message ?? "Unknown disconnect reason";
}

function shouldResetAuthState(statusCode: number | undefined, message: string): boolean {
  return (
    statusCode === DisconnectReason.loggedOut ||
    statusCode === 401 ||
    statusCode === 403 ||
    message.includes("bad session") ||
    message.includes("Bad Session")
  );
}

function isInsidePairingWindow(): boolean {
  return isPairingPending && Date.now() - lastPairingCodeAt < env.WA_PAIRING_WAIT_MS;
}

function getPairingWaitRemainingMs(): number {
  if (!isPairingPending) return 0;
  return Math.max(0, env.WA_PAIRING_WAIT_MS - (Date.now() - lastPairingCodeAt));
}

function isRecoverableBaileysError(error: unknown): boolean {
  const message = getErrorMessage(error);
  const statusCode = getDisconnectStatusCode(error);

  return (
    statusCode === 408 ||
    statusCode === 515 ||
    message.includes("Timed Out") ||
    message.includes("Request Time-out") ||
    message.includes("Stream Errored")
  );
}

function registerProcessHandlers(): void {
  if (processHandlersRegistered) return;
  processHandlersRegistered = true;

  process.on("unhandledRejection", (reason) => {
    logger.error({ step: "unhandled_rejection", reason }, "Unhandled promise rejection");

    if (isRecoverableBaileysError(reason)) {
      const statusCode = getDisconnectStatusCode(reason);
      const message = getErrorMessage(reason);

      if (statusCode === 515) {
        logger.warn(
          { step: "connection_restart_required", statusCode, recoverable: true },
          "WhatsApp stream error 515 detected, reconnect will be scheduled"
        );
      }

      if (statusCode === 408 || message.includes("Timed Out") || message.includes("Request Time-out")) {
        logger.warn(
          { step: "connection_timeout", statusCode, recoverable: true },
          "WhatsApp query timeout detected, reconnect will be scheduled"
        );
      }

      scheduleReconnect("unhandled_recoverable_baileys_error");
    }
  });

  process.on("uncaughtException", (error) => {
    logger.error({ step: "uncaught_exception", err: error }, "Uncaught exception");

    if (isRecoverableBaileysError(error)) {
      const statusCode = getDisconnectStatusCode(error);
      const message = getErrorMessage(error);

      if (statusCode === 515) {
        logger.warn(
          { step: "connection_restart_required", statusCode, recoverable: true },
          "WhatsApp stream error 515 detected, reconnect will be scheduled"
        );
      }

      if (statusCode === 408 || message.includes("Timed Out") || message.includes("Request Time-out")) {
        logger.warn(
          { step: "connection_timeout", statusCode, recoverable: true },
          "WhatsApp query timeout detected, reconnect will be scheduled"
        );
      }

      scheduleReconnect("uncaught_recoverable_baileys_error");
      return;
    }

    process.exit(1);
  });
}
