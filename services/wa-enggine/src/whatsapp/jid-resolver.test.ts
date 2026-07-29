import assert from "node:assert/strict";
import test from "node:test";

import { resolveCanonicalJid } from "./jid-resolver";

function socketWithResolver(resolver: (jid: string) => Promise<string | null>) {
  return {
    signalRepository: {
      lidMapping: {
        getPNForLID: resolver,
      },
    },
  };
}

test("resolves a Baileys LID to the canonical phone JID", async () => {
  const socket = socketWithResolver(async () => "628123@s.whatsapp.net");
  assert.equal(await resolveCanonicalJid(socket, "123@lid"), "628123@s.whatsapp.net");
});

test("keeps a phone JID without consulting the LID mapping", async () => {
  let called = false;
  const socket = socketWithResolver(async () => {
    called = true;
    return null;
  });
  assert.equal(
    await resolveCanonicalJid(socket, "628123@s.whatsapp.net"),
    "628123@s.whatsapp.net",
  );
  assert.equal(called, false);
});

test("keeps the LID when Baileys cannot resolve it", async () => {
  const socket = socketWithResolver(async () => {
    throw new Error("mapping unavailable");
  });
  assert.equal(await resolveCanonicalJid(socket, "123@lid"), "123@lid");
});
