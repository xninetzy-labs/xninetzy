import { useMultiFileAuthState } from "@whiskeysockets/baileys";
import fs from "node:fs/promises";
import path from "node:path";

import { env } from "../config/env";
import { logger } from "../utils/logger";

export async function createAuthState() {
  logger.info({ step: "auth_loading", authDir: env.WA_AUTH_DIR }, "Loading WhatsApp auth state");

  const authState = await useMultiFileAuthState(env.WA_AUTH_DIR);

  logger.info(
    {
      step: "auth_loaded",
      registered: authState.state.creds.registered,
    },
    "WhatsApp auth state loaded"
  );

  return authState;
}

export async function clearAuthState(): Promise<void> {
  const authDir = path.resolve(env.WA_AUTH_DIR);
  const cwd = path.resolve(process.cwd());

  if (authDir === cwd || authDir === path.parse(authDir).root || authDir.length < cwd.length) {
    throw new Error(`Refusing to remove unsafe WhatsApp auth directory: ${authDir}`);
  }

  logger.warn({ step: "session_cleanup", authDir: env.WA_AUTH_DIR }, "Cleaning WhatsApp auth session directory");

  const entries = await fs.readdir(authDir, { withFileTypes: true }).catch((error: NodeJS.ErrnoException) => {
    if (error.code === "ENOENT") return [];
    throw error;
  });

  await Promise.all(
    entries.map((entry) => fs.rm(path.join(authDir, entry.name), { recursive: true, force: true }))
  );
}
