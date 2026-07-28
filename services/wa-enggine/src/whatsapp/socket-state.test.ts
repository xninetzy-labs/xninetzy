import assert from "node:assert/strict";
import test from "node:test";

import type { WASocket } from "@whiskeysockets/baileys";

import {
  getConnectionStatus,
  isSocketReady,
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
