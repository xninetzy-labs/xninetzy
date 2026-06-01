import dotenv from "dotenv";
import path from "node:path";

dotenv.config();
dotenv.config({ path: path.resolve(process.cwd(), "../../.env") });

function parseNumber(value: string | undefined, fallback: number): number {
  if (!value) return fallback;

  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export type WaLoginMode = "qr" | "pairing_code";

function getWaLoginMode(): WaLoginMode {
  const raw = (process.env.WA_LOGIN_MODE || "qr").trim().toLowerCase();

  if (raw === "pairing_code" || raw === "pairing-code" || raw === "code") {
    return "pairing_code";
  }

  if (raw === "qr") {
    return "qr";
  }

  return "qr";
}

const WA_LOGIN_MODE = getWaLoginMode();
const WA_LOGIN_MODE_RAW = process.env.WA_LOGIN_MODE || "qr";
const WA_PHONE_NUMBER = process.env.WA_PHONE_NUMBER?.replace(/\D/g, "") || "";

export const env = {
  WA_AUTH_DIR:
    process.env.WA_AUTH_DIR ??
    process.env.WA_SESSION_DIR ??
    path.resolve(process.cwd(), "sessions"),
  WA_LOGIN_MODE,
  WA_LOGIN_MODE_RAW,
  WA_PHONE_NUMBER,
  WA_CONNECT_TIMEOUT_MS: parseNumber(process.env.WA_CONNECT_TIMEOUT_MS, 60_000),
  WA_QUERY_TIMEOUT_MS: parseNumber(process.env.WA_QUERY_TIMEOUT_MS, 60_000),
  WA_KEEP_ALIVE_INTERVAL_MS: parseNumber(process.env.WA_KEEP_ALIVE_INTERVAL_MS, 30_000),
  WA_PAIRING_WAIT_MS: parseNumber(process.env.WA_PAIRING_WAIT_MS, 90_000),
  WA_PAIRING_RECONNECT_DELAY_MS: parseNumber(process.env.WA_PAIRING_RECONNECT_DELAY_MS, 30_000),
  WA_GROUP_TRIGGER_MODE: process.env.WA_GROUP_TRIGGER_MODE ?? "mention_or_prefix",
  WA_COMMAND_PREFIX: process.env.WA_COMMAND_PREFIX ?? "!",
  WA_GROUP_ALLOW_ALL: process.env.WA_GROUP_ALLOW_ALL === "true",
  WA_GROUP_TREAT_ANY_MENTION_AS_BOT: process.env.WA_GROUP_TREAT_ANY_MENTION_AS_BOT === "true",
  AI_BASE_URL: process.env.AI_BASE_URL ?? process.env.AI_API_URL ?? "http://ai:8000",
  AI_CHAT_ENDPOINT: process.env.AI_CHAT_ENDPOINT ?? "/api/chat",
  AI_TIMEOUT_MS: parseNumber(process.env.AI_TIMEOUT_MS, 60_000),
  AI_API_URL: process.env.AI_BASE_URL ?? process.env.AI_API_URL ?? "http://ai:8000",
  MCP_SERVER_ENABLED: process.env.MCP_SERVER_ENABLED !== "false",
  MCP_HOST: process.env.MCP_HOST ?? "0.0.0.0",
  MCP_PORT: parseNumber(process.env.MCP_PORT, 8081),
  MCP_API_KEY: process.env.WA_MCP_API_KEY ?? process.env.MCP_API_KEY ?? "",
  BOT_NAME: process.env.BOT_NAME ?? "Xninetzy AI",
  BOT_OWNER: process.env.BOT_OWNER ?? "Misbahul Muttaqin",
};

export function validateEnv(): void {
  if (env.WA_LOGIN_MODE === "pairing_code" && !env.WA_PHONE_NUMBER) {
    throw new Error("WA_PHONE_NUMBER is required when WA_LOGIN_MODE=pairing_code");
  }
}
