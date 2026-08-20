import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  STARTUP_MENU_CARDS,
  normalizeStartupMenuJid,
  resetStartupMenuState,
  sendStartupAdminMenuOnce,
  startupMenuFallbackText,
  type StartupMenuOptions,
} from "./startup-menu";

function options(): StartupMenuOptions {
  const stateDir = fs.mkdtempSync(path.join(os.tmpdir(), "xninetzy-startup-menu-"));
  return {
    enabled: true,
    adminJid: "628123456789@s.whatsapp.net",
    delayMs: 0,
    botName: "Xninetzy OS",
    statePath: path.join(stateDir, "startup-menu.json"),
  };
}

test("startup menu exposes fifteen unique command buttons", () => {
  const buttons = STARTUP_MENU_CARDS.flatMap((card) => card.buttons);

  assert.equal(STARTUP_MENU_CARDS.length, 5);
  assert.equal(buttons.length, 15);
  assert.equal(new Set(buttons.map((button) => button.id)).size, buttons.length);
  assert.equal(STARTUP_MENU_CARDS.every((card) => card.buttons.length <= 3), true);
  assert.equal(buttons.every((button) => button.id.startsWith("/")), true);
});

test("startup menu sends every card only once across reconnects and restarts", async () => {
  resetStartupMenuState();
  const sent: Array<{ jid: string; content: unknown }> = [];
  const sock = {
    async sendMessage(jid: string, content: unknown) {
      sent.push({ jid, content });
      return {};
    },
  };

  const startupOptions = options();
  const first = await sendStartupAdminMenuOnce(sock as never, startupOptions);
  const reconnect = await sendStartupAdminMenuOnce(sock as never, startupOptions);
  resetStartupMenuState();
  const restart = await sendStartupAdminMenuOnce(sock as never, startupOptions);

  assert.deepEqual(first, { status: "sent", messagesSent: 5 });
  assert.deepEqual(reconnect, { status: "already_handled", messagesSent: 0 });
  assert.deepEqual(restart, { status: "already_handled", messagesSent: 0 });
  assert.equal(sent.length, 5);
  assert.equal(sent.every((message) => message.jid === startupOptions.adminJid), true);
});

test("startup menu falls back to complete text when buttons fail", async () => {
  resetStartupMenuState();
  const sent: unknown[] = [];
  let attempts = 0;
  const sock = {
    async sendMessage(_jid: string, content: unknown) {
      attempts += 1;
      if (attempts === 1) throw new Error("buttons unsupported");
      sent.push(content);
      return {};
    },
  };

  const startupOptions = options();
  const result = await sendStartupAdminMenuOnce(sock as never, startupOptions);
  const fallback = startupMenuFallbackText(startupOptions.botName);

  assert.deepEqual(result, { status: "fallback", messagesSent: 1 });
  assert.equal(sent.length, 1);
  assert.match(fallback, /\/today/);
  assert.match(fallback, /\/hebat-login/);
  assert.match(fallback, /\/agent/);
});

test("startup menu skips safely without an admin jid", async () => {
  resetStartupMenuState();
  let calls = 0;
  const sock = {
    async sendMessage() {
      calls += 1;
      return {};
    },
  };

  const result = await sendStartupAdminMenuOnce(sock as never, {
    ...options(),
    adminJid: "",
  });

  assert.deepEqual(result, { status: "skipped", messagesSent: 0 });
  assert.equal(calls, 0);
  assert.equal(normalizeStartupMenuJid("628123456789"), "628123456789@s.whatsapp.net");
});
