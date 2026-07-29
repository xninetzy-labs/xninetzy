import assert from "node:assert/strict";
import test from "node:test";
import { mcpCallLogFields } from "./logging";

test("MCP logging keeps only tool identity and sorted input keys", () => {
  const fields = mcpCallLogFields({
    tool: "send_text_message",
    input: {
      text: "verified token 12345",
      jid: "628123@s.whatsapp.net",
    },
  });

  assert.deepEqual(fields, {
    tool: "send_text_message",
    inputKeys: ["jid", "text"],
  });
  assert.equal(JSON.stringify(fields).includes("12345"), false);
  assert.equal(JSON.stringify(fields).includes("628123"), false);
});

test("MCP logging fails closed for malformed payloads", () => {
  assert.deepEqual(mcpCallLogFields("secret"), {
    tool: "unknown",
    inputKeys: [],
  });
});
