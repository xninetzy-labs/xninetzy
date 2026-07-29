import assert from "node:assert/strict";
import test from "node:test";

import { extractMessageText } from "./message-parser";

test("button reply uses command id instead of display label", () => {
  const text = extractMessageText({
    buttonsResponseMessage: {
      selectedButtonId: "/approve 42",
      selectedDisplayText: "Approve",
    },
  });

  assert.equal(text, "/approve 42");
});

test("template reply uses command id instead of display label", () => {
  const text = extractMessageText({
    templateButtonReplyMessage: {
      selectedId: "/reject 42",
      selectedDisplayText: "Reject",
    },
  });

  assert.equal(text, "/reject 42");
});
