import type { WASocket } from "@whiskeysockets/baileys";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import { maskPhone } from "../utils/observability";

let pairingRequested = false;
let isPairingPending = false;
let lastPairingCodeAt = 0;

export function getPairingState() {
  return { pairingRequested, isPairingPending, lastPairingCodeAt };
}

export function resetPairingState(): void {
  pairingRequested = false;
  isPairingPending = false;
  lastPairingCodeAt = 0;
}

export function isInsidePairingWindow(): boolean {
  return isPairingPending && Date.now() - lastPairingCodeAt < env.WA_PAIRING_WAIT_MS;
}

export function getPairingWaitRemainingMs(): number {
  if (!isPairingPending) return 0;
  return Math.max(0, env.WA_PAIRING_WAIT_MS - (Date.now() - lastPairingCodeAt));
}

export async function requestPairingCodeIfNeeded(currentSock: WASocket, registered: boolean): Promise<void> {
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
