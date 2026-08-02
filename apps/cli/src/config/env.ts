import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

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

  toolTimeoutMs: number;
  mcpConnectTimeoutMs: number;
  mcpCallTimeoutMs: number;

  slowRequestWarningMs: number;

  aiApiKey: string;

  envFilePath: string | null;
  envLoaded: boolean;
}

function parseEnv(raw: string): Record<string, string> {
  const values: Record<string, string> = {};

  for (const rawLine of raw.split(/\r?\n/)) {
    let line = rawLine.trim();

    if (!line || line.startsWith('#')) {
      continue;
    }

    if (line.startsWith('export ')) {
      line = line.slice('export '.length).trim();
    }

    const separator = line.indexOf('=');

    if (separator === -1) {
      continue;
    }

    const key = line.slice(0, separator).trim();
    let value = line.slice(separator + 1).trim();

    if (!key) {
      continue;
    }

    const doubleQuoted =
      value.startsWith('"') &&
      value.endsWith('"');

    const singleQuoted =
      value.startsWith("'") &&
      value.endsWith("'");

    if (doubleQuoted || singleQuoted) {
      value = value.slice(1, -1);
    }

    values[key] = value;
  }

  return values;
}

function findEnvFile(start: string): string | null {
  let current = resolve(start);

  for (let depth = 0; depth < 8; depth += 1) {
    const candidate = join(current, '.env');

    if (existsSync(candidate)) {
      return candidate;
    }

    const parent = dirname(current);

    if (parent === current) {
      break;
    }

    current = parent;
  }

  return null;
}

function loadRootEnv(): string | null {
  const entryDirectory = dirname(
    fileURLToPath(import.meta.url)
  );

  const envFile =
    findEnvFile(process.cwd()) ??
    findEnvFile(entryDirectory);

  if (!envFile) {
    return null;
  }

  const raw = readFileSync(envFile, 'utf8');
  const values = parseEnv(raw);

  for (const [key, value] of Object.entries(values)) {
    process.env[key] ??= value;
  }

  return envFile;
}

function positiveInteger(
  value: string | undefined,
  fallback: number
): number {
  if (!value) {
    return fallback;
  }

  const parsed = Number(value);

  return Number.isInteger(parsed) && parsed > 0
    ? parsed
    : fallback;
}

function positiveMilliseconds(
  value: string | undefined,
  fallbackMilliseconds: number
): number {
  return positiveInteger(value, fallbackMilliseconds);
}

function positiveSeconds(
  value: string | undefined,
  fallbackSeconds: number
): number {
  return positiveInteger(value, fallbackSeconds) * 1000;
}

const envFilePath = loadRootEnv();

export const cliConfig: Readonly<CliConfig> = {
  aiUrl:
    process.env.XNINETZY_AI_URL ??
    process.env.AI_API_URL ??
    process.env.AI_BASE_URL ??
    'http://localhost:8000',

  chatId:
    process.env.XNINETZY_CLI_CHAT_ID ??
    'xninetzy-cli',

  senderId:
    process.env.XNINETZY_CLI_SENDER_ID ??
    process.env.OWNER_PHONE_NUMBER ??
    process.env.ADMIN_JID ??
    'mcp:local-owner',

  senderName:
    process.env.XNINETZY_CLI_SENDER_NAME ??
    process.env.OWNER_ALIAS ??
    process.env.BOT_OWNER ??
    'Local Owner',

  requestTimeoutMs: positiveMilliseconds(
    process.env.XNINETZY_CLI_TIMEOUT_MS,
    120_000
  ),

  thinkTimeoutMs: positiveSeconds(
    process.env.XNINETZY_THINK_TIMEOUT_SECONDS,
    120
  ),

  inactivityTimeoutMs: positiveSeconds(
    process.env.XNINETZY_INACTIVITY_TIMEOUT_SECONDS,
    60
  ),

  streamTimeoutMs: positiveSeconds(
    process.env.XNINETZY_STREAM_TIMEOUT_SECONDS,
    300
  ),

  deepResearchTimeoutMs: positiveSeconds(
    process.env.XNINETZY_DEEP_RESEARCH_TIMEOUT_SECONDS,
    900
  ),

  toolTimeoutMs: positiveSeconds(
    process.env.XNINETZY_TOOL_TIMEOUT_SECONDS,
    180
  ),

  mcpConnectTimeoutMs: positiveSeconds(
    process.env.XNINETZY_MCP_CONNECT_TIMEOUT_SECONDS,
    20
  ),

  mcpCallTimeoutMs: positiveSeconds(
    process.env.XNINETZY_MCP_CALL_TIMEOUT_SECONDS,
    180
  ),

  slowRequestWarningMs: positiveSeconds(
    process.env.XNINETZY_SLOW_REQUEST_WARNING_SECONDS,
    45
  ),

  aiApiKey:
    process.env.AI_API_KEY ??
    '',

  envFilePath,

  envLoaded: Boolean(envFilePath)
};
