import { env } from "./config/env";
import { validateEnv } from "./config/env";
import { startWhatsAppSocket } from "./whatsapp/socket";
import { logger } from "./utils/logger";
import fs from "node:fs";

async function main(): Promise<void> {
  if (
    !["qr", "pairing_code", "pairing-code", "code"].includes(env.WA_LOGIN_MODE_RAW.trim().toLowerCase())
  ) {
    logger.warn(
      {
        step: "config_invalid_login_mode",
        raw: env.WA_LOGIN_MODE_RAW,
        fallback: "qr",
      },
      "Invalid WA_LOGIN_MODE. Falling back to QR mode."
    );
  }

  if (env.WA_LOGIN_MODE === "pairing_code" && !env.WA_PHONE_NUMBER) {
    logger.error(
      {
        step: "config_invalid",
        loginMode: env.WA_LOGIN_MODE,
        hasPhoneNumber: false,
      },
      "WA_LOGIN_MODE=pairing_code requires WA_PHONE_NUMBER"
    );
  }

  validateEnv();

  logger.info(
    {
      step: "service_boot",
      service: "wa-enggine",
      nodeEnv: process.env.NODE_ENV,
      authDir: env.WA_AUTH_DIR,
      logLevel: process.env.WA_LOG_LEVEL ?? process.env.LOG_LEVEL ?? "info",
    },
    "WA engine service booting"
  );

  if (!fs.existsSync("/.dockerenv")) {
    logger.warn(
      {
        step: "local_dev_warning",
        authDir: env.WA_AUTH_DIR,
      },
      "Running wa-enggine locally. Do not run Docker wa-enggine at the same time for the same WhatsApp account."
    );
  }

  logger.info(
    {
      step: "config_loaded",
      loginMode: env.WA_LOGIN_MODE,
      qrMode: env.WA_LOGIN_MODE === "qr",
      pairingMode: env.WA_LOGIN_MODE === "pairing_code",
      hasPhoneNumber: Boolean(env.WA_PHONE_NUMBER),
      authDir: env.WA_AUTH_DIR,
      connectTimeoutMs: env.WA_CONNECT_TIMEOUT_MS,
      queryTimeoutMs: env.WA_QUERY_TIMEOUT_MS,
      keepAliveIntervalMs: env.WA_KEEP_ALIVE_INTERVAL_MS,
      syncFullHistory: false,
      markOnlineOnConnect: false,
    },
    "WA engine config loaded"
  );

  await startWhatsAppSocket();
}

main().catch((error) => {
  logger.error({ step: "service_boot_failed", err: error }, "WhatsApp worker failed to start");
  process.exit(1);
});
