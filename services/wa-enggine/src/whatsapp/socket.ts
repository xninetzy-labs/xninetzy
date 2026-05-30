import type { WASocket } from "@whiskeysockets/baileys";
import { logger } from "../utils/logger";
import { createAuthState } from "./auth";
import { createWhatsAppSocket } from "./socket-factory";
import { handleConnectionUpdate, resetAuthStateAndScheduleReconnect } from "./connection-handler";
import { registerMessageListener } from "./message-listener";
import { registerProcessHandlers } from "./process-handlers";
import { requestPairingCodeIfNeeded } from "./pairing-manager";
import { cleanupCurrentSocket, setCurrentSocket, getCurrentSocket } from "./socket-state";
import { getDisconnectStatusCode, getErrorMessage, shouldResetAuthState } from "./disconnect-utils";
import { scheduleReconnect } from "./reconnect-manager";

let isStarting = false;

export async function startWhatsAppSocket(): Promise<void> {
  registerProcessHandlers();

  logger.info(
    {
      step: "start_requested",
      isStarting,
      hasSocket: Boolean(getCurrentSocket()),
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
    cleanupCurrentSocket("replace_socket_before_start");

    const { state, saveCreds } = await createAuthState();
    const sock = await createWhatsAppSocket(state);

    setCurrentSocket(sock);

    sock.ev.on("creds.update", async () => {
      await saveCreds();
    });

    sock.ev.on("connection.update", (update) => {
      void handleConnectionUpdate(sock, update);
    });

    registerMessageListener(sock);
    await requestPairingCodeIfNeeded(sock, state.creds.registered);
  } catch (error) {
    const statusCode = getDisconnectStatusCode(error);
    const message = getErrorMessage(error);
    
    logger.error({ step: "start_failed", statusCode, err: error }, "Failed to start WhatsApp");

    if (shouldResetAuthState(statusCode, message)) {
      await resetAuthStateAndScheduleReconnect(`start_failed_${statusCode ?? "unknown"}`);
      return;
    }

    scheduleReconnect("start_failed");
  } finally {
    isStarting = false;
  }
}
