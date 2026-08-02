import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export interface CliConfig {
  aiUrl: string;
  chatId: string;
  senderId: string;
  senderName: string;
  requestTimeoutMs: number;
  thinkTimeoutMs: number;
  inactivityTimeoutMs: number;
  streamTimeoutMs: number;
  deepResearchTimeoutMs: number;
  slowRequestWarningMs: number;
  aiApiKey: string;
  envFilePath: string | null;
  envLoaded: boolean;
}

function parseEnv(raw: string): Record<string, string> {
  const values: Record<string, string> = {};

  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const separator = trimmed.indexOf("=");
    if (separator === -1) continue;

    const key = trimmed.slice(0, separator).trim();
    let value = trimmed.slice(separator + 1).trim();
    if (!key) continue;

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    values[key] = value;
  }

  return values;
}

function findEnvFile(start: string): string | null {
  let current = resolve(start);

  for (let i = 0; i < 8; i += 1) {
    const candidate = join(current, ".env");
    if (existsSync(candidate)) return candidate;

    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }

  return null;
}

function loadRootEnv(): string | null {
  const entryDir = dirname(fileURLToPath(import.meta.url));
  const envFile =
    findEnvFile(process.cwd()) ??
    findEnvFile(entryDir);

  if (!envFile) return null;

  const values = parseEnv(readFileSync(envFile, "utf8"));
  for (const [key, value] of Object.entries(values)) {
    process.env[key] ??= value;
  }

  return envFile;
}

const envFilePath = loadRootEnv();

function positiveInteger(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function positiveSeconds(value: string | undefined, fallback: number): number {
  return positiveInteger(value, fallback) * 1000;
}

export const cliConfig: CliConfig = {
  aiUrl:
    process.env.XNINETZY_AI_URL ??
    process.env.AI_API_URL ??
    process.env.AI_BASE_URL ??
    "http://localhost:8000",
  chatId: process.env.XNINETZY_CLI_CHAT_ID ?? 'xninetzy-cli',
  senderId:
    process.env.XNINETZY_CLI_SENDER_ID ??
    process.env.OWNER_PHONE_NUMBER ??
    process.env.ADMIN_JID ??
    'mcp:local-owner',
  senderName: process.env.XNINETZY_CLI_SENDER_NAME ?? process.env.OWNER_ALIAS ?? process.env.BOT_OWNER ?? 'Local Owner',
  requestTimeoutMs: positiveInteger(process.env.XNINETZY_CLI_TIMEOUT_MS, 120_000),
  thinkTimeoutMs: positiveSeconds(process.env.XNINETZY_THINK_TIMEOUT_SECONDS, 120),
  inactivityTimeoutMs: positiveSeconds(process.env.XNINETZY_INACTIVITY_TIMEOUT_SECONDS, 60),
  streamTimeoutMs: positiveSeconds(process.env.XNINETZY_STREAM_TIMEOUT_SECONDS, 300),
  deepResearchTimeoutMs: positiveSeconds(process.env.XNINETZY_DEEP_RESEARCH_TIMEOUT_SECONDS, 900),
  slowRequestWarningMs: positiveSeconds(process.env.XNINETZY_SLOW_REQUEST_WARNING_SECONDS, 45),
  aiApiKey: process.env.AI_API_KEY ?? '',
  envFilePath,
  envLoaded: Boolean(envFilePath),
};
