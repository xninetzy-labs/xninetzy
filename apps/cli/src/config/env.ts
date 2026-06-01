import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export interface CliConfig {
  aiUrl: string;
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

export const cliConfig: CliConfig = {
  aiUrl:
    process.env.XNINETZY_AI_URL ??
    process.env.AI_API_URL ??
    process.env.AI_BASE_URL ??
    "http://localhost:8000",
  envFilePath,
  envLoaded: Boolean(envFilePath),
};
