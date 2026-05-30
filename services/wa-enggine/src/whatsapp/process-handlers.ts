import { logger } from "../utils/logger";
import { isRecoverableBaileysError, getDisconnectStatusCode, getErrorMessage } from "./disconnect-utils";
import { scheduleReconnect } from "./reconnect-manager";

let processHandlersRegistered = false;

export function registerProcessHandlers(): void {
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
