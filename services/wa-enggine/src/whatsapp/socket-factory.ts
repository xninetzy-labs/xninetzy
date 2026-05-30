import makeWASocket, {
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  type AuthenticationState,
  type WASocket,
} from "@whiskeysockets/baileys";
import { env } from "../config/env";
import { logger } from "../utils/logger";

const baileysLogger = logger.child({ component: "baileys" });
baileysLogger.level = (process.env.WA_BAILEYS_LOG_LEVEL || "warn") as any;

export async function createWhatsAppSocket(state: AuthenticationState): Promise<WASocket> {
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
    },
    "Creating WhatsApp socket"
  );

  const sock = makeWASocket({
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

  return sock;
}
