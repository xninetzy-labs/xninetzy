import { DisconnectReason } from "@whiskeysockets/baileys";
import type { Boom } from "@hapi/boom";

export function getDisconnectStatusCode(error: unknown): number | undefined {
  return (
    (error as Boom | undefined)?.output?.statusCode ??
    (error as { data?: { statusCode?: number } } | undefined)?.data?.statusCode ??
    (error as { statusCode?: number } | undefined)?.statusCode
  );
}

export function getErrorMessage(error: unknown): string {
  return (error as { message?: string } | undefined)?.message ?? "Unknown disconnect reason";
}

export function shouldResetAuthState(statusCode: number | undefined, message: string): boolean {
  return (
    statusCode === DisconnectReason.loggedOut ||
    statusCode === 401 ||
    statusCode === 403 ||
    message.includes("bad session") ||
    message.includes("Bad Session")
  );
}

export function isRecoverableBaileysError(error: unknown): boolean {
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
