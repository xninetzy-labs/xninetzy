import fs from "node:fs";
import path from "node:path";
import type { WASocket } from "@whiskeysockets/baileys";

import { env } from "../config/env";
import { logger } from "../utils/logger";
import { maskJid } from "../utils/observability";
import { normalizeDigits, stripDeviceSuffix } from "../utils/jid";

export type StartupMenuButton = {
  id: string;
  label: string;
};

export type StartupMenuCard = {
  title: string;
  description: string;
  buttons: StartupMenuButton[];
};

export type StartupMenuOptions = {
  enabled: boolean;
  adminJid: string;
  delayMs: number;
  botName: string;
  statePath?: string;
};

export type StartupMenuResult = {
  status: "sent" | "fallback" | "skipped" | "already_handled" | "failed";
  messagesSent: number;
};

type StartupMenuSocket = Pick<WASocket, "sendMessage">;
type StartupMenuState = "idle" | "sending" | "handled";
type StartupMenuManifest = {
  version: 1;
  chats: Record<string, number>;
};

let startupMenuState: StartupMenuState = "idle";

export const STARTUP_MENU_CARDS: StartupMenuCard[] = [
  {
    title: "🧭 Harian",
    description: "Tentukan fokus, rapikan inbox, lalu tutup hari dengan review.",
    buttons: [
      { id: "/today", label: "Fokus Hari Ini" },
      { id: "/inbox", label: "OS Inbox" },
      { id: "/review", label: "Review Harian" },
    ],
  },
  {
    title: "✅ Life OS",
    description: "Kelola komitmen, arah, dan aktivitas personal.",
    buttons: [
      { id: "/tasks", label: "Daftar Task" },
      { id: "/goals", label: "Goal Aktif" },
      { id: "/workout", label: "Workout" },
    ],
  },
  {
    title: "🎓 Akademik",
    description: "Masuk HEBAT, cek ringkasan kuliah, lalu lanjutkan roadmap.",
    buttons: [
      { id: "/hebat-login", label: "Login HEBAT" },
      { id: "/hebat", label: "Ringkasan HEBAT" },
      { id: "/roadmaps", label: "Roadmap" },
    ],
  },
  {
    title: "🧠 Belajar & Knowledge",
    description: "Tentukan fokus belajar dan gunakan memori serta skills bersama.",
    buttons: [
      { id: "/study-today", label: "Belajar Hari Ini" },
      { id: "/memory", label: "Memory" },
      { id: "/skills", label: "Skills" },
    ],
  },
  {
    title: "⚙️ Kontrol AI",
    description: "Periksa approval, provider LLM, dan coding runtime.",
    buttons: [
      { id: "/approvals", label: "Approval" },
      { id: "/llm", label: "Provider LLM" },
      { id: "/agent", label: "Coding Agent" },
    ],
  },
];

function startupMenuOptions(): StartupMenuOptions {
  return {
    enabled: env.WA_STARTUP_MENU_ENABLED,
    adminJid: env.ADMIN_JID,
    delayMs: env.WA_STARTUP_MENU_DELAY_MS,
    botName: env.BOT_NAME,
    statePath: startupMenuStorePath(),
  };
}

function startupMenuStorePath(): string {
  return path.resolve(env.WA_PROCESSING_DIR, "startup-menu.json");
}

function loadStartupMenuManifest(statePath: string): StartupMenuManifest {
  try {
    const parsed = JSON.parse(fs.readFileSync(statePath, "utf8")) as StartupMenuManifest;
    if (parsed.version !== 1 || !parsed.chats || typeof parsed.chats !== "object") {
      throw new Error("Invalid startup-menu manifest");
    }
    return parsed;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return { version: 1, chats: {} };
    }
    throw error;
  }
}

function saveStartupMenuManifest(statePath: string, manifest: StartupMenuManifest): void {
  fs.mkdirSync(path.dirname(statePath), { recursive: true });
  const temporary = `${statePath}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(manifest, null, 2), { mode: 0o600 });
  fs.renameSync(temporary, statePath);
}

function hasStartupMenu(statePath: string, chatId: string): boolean {
  return Boolean(loadStartupMenuManifest(statePath).chats[chatId]);
}

function markStartupMenuSent(statePath: string, chatId: string): void {
  const manifest = loadStartupMenuManifest(statePath);
  manifest.chats[chatId] = Date.now();
  saveStartupMenuManifest(statePath, manifest);
}

export function normalizeStartupMenuJid(value: string): string {
  const normalized = stripDeviceSuffix(value.trim());
  if (normalized.includes("@")) return normalized;
  const digits = normalizeDigits(normalized);
  return digits ? `${digits}@s.whatsapp.net` : "";
}

export function startupMenuFallbackText(botName: string): string {
  const lines = [
    `🚀 *${botName} siap digunakan*`,
    "",
    "Interactive button tidak tersedia. Gunakan command berikut:",
  ];
  for (const card of STARTUP_MENU_CARDS) {
    lines.push("", `*${card.title}*`);
    for (const button of card.buttons) {
      lines.push(`• ${button.label}: ${button.id}`);
    }
  }
  lines.push("", "Kirim `/commands` untuk katalog tool aktif atau `/helper` untuk panduan lengkap.");
  return lines.join("\n");
}

export async function sendStartupAdminMenuOnce(
  sock: StartupMenuSocket,
  options: StartupMenuOptions = startupMenuOptions(),
): Promise<StartupMenuResult> {
  if (startupMenuState !== "idle") {
    return { status: "already_handled", messagesSent: 0 };
  }

  const adminJid = normalizeStartupMenuJid(options.adminJid);
  if (!options.enabled || !adminJid) {
    startupMenuState = "handled";
    logger.info(
      {
        step: "startup_menu_skipped",
        enabled: options.enabled,
        hasAdminJid: Boolean(adminJid),
      },
      "WhatsApp startup menu skipped",
    );
    return { status: "skipped", messagesSent: 0 };
  }

  const statePath = options.statePath || startupMenuStorePath();
  if (hasStartupMenu(statePath, adminJid)) {
    startupMenuState = "handled";
    return { status: "already_handled", messagesSent: 0 };
  }

  startupMenuState = "sending";
  if (options.delayMs > 0) {
    await new Promise((resolve) => setTimeout(resolve, options.delayMs));
  }

  let messagesSent = 0;
  try {
    for (const [index, card] of STARTUP_MENU_CARDS.entries()) {
      const heading = index === 0
        ? `🚀 *${options.botName} siap digunakan*\n\n${card.title}`
        : card.title;
      await sock.sendMessage(
        adminJid,
        {
          text: `${heading}\n${card.description}`,
          footer: `${options.botName} • Admin menu`,
          buttons: card.buttons.map((button) => ({
            buttonId: button.id,
            buttonText: { displayText: button.label },
            type: 1,
          })),
          headerType: 1,
        } as never,
      );
      messagesSent += 1;
    }
    markStartupMenuSent(statePath, adminJid);
    startupMenuState = "handled";
    logger.info(
      {
        step: "startup_menu_sent",
        jid: maskJid(adminJid),
        messagesSent,
        buttonsSent: STARTUP_MENU_CARDS.reduce(
          (total, card) => total + card.buttons.length,
          0,
        ),
      },
      "WhatsApp startup menu sent to admin",
    );
    return { status: "sent", messagesSent };
  } catch (buttonError) {
    logger.warn(
      {
        step: "startup_menu_button_failed",
        jid: maskJid(adminJid),
        messagesSent,
        err: buttonError,
      },
      "Interactive startup menu failed; sending text fallback",
    );
  }

  try {
    await sock.sendMessage(adminJid, {
      text: startupMenuFallbackText(options.botName),
    });
    markStartupMenuSent(statePath, adminJid);
    startupMenuState = "handled";
    return { status: "fallback", messagesSent: messagesSent + 1 };
  } catch (fallbackError) {
    startupMenuState = "idle";
    logger.error(
      {
        step: "startup_menu_failed",
        jid: maskJid(adminJid),
        err: fallbackError,
      },
      "WhatsApp startup menu delivery failed",
    );
    return { status: "failed", messagesSent };
  }
}

export function resetStartupMenuState(): void {
  startupMenuState = "idle";
}
