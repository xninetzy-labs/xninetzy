import assert from "node:assert/strict";
import test from "node:test";

import type { WASocket } from "@whiskeysockets/baileys";

import {
  clearActiveCaptchaChallenge,
  getConnectionStatus,
  isSocketReady,
  rememberCaptchaChallenge,
  resolveActiveCaptchaCommand,
  setConnectionStatus,
  setCurrentSocket,
} from "./socket-state";

test("socket readiness requires an open connection", () => {
  setCurrentSocket({} as WASocket);
  setConnectionStatus("connecting");
  assert.equal(isSocketReady(), false);
  assert.equal(getConnectionStatus(), "connecting");

  setConnectionStatus("open");
  assert.equal(isSocketReady(), true);

  setCurrentSocket(null);
  assert.equal(isSocketReady(), false);
  assert.equal(getConnectionStatus(), "disconnected");
});

test("active captcha accepts a bare answer only from the configured target", () => {
  clearActiveCaptchaChallenge();
  rememberCaptchaChallenge(
    "628123@s.whatsapp.net",
    "Balas: /captcha challenge_123 JAWABAN\nBerlaku sampai: 2099-01-01T00:00:00Z",
  );

  assert.equal(
    resolveActiveCaptchaCommand("A9Z2", "628123:7@s.whatsapp.net", 1),
    "/captcha challenge_123 A9Z2",
  );
  assert.equal(resolveActiveCaptchaCommand("A9Z2", "628999@s.whatsapp.net", 1), null);
  assert.equal(resolveActiveCaptchaCommand("pesan biasa dua kata", "628123@s.whatsapp.net", 1), null);
  clearActiveCaptchaChallenge();
});
