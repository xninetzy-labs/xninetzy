import assert from "node:assert/strict";
import test from "node:test";

import { isSensitiveSignalLog } from "./console-redaction";

test("signal session objects are classified as sensitive log material", () => {
  assert.equal(isSensitiveSignalLog(["Closing session:", { privateKey: "secret" }]), true);
  assert.equal(isSensitiveSignalLog(["Session already closed", { rootKey: "secret" }]), true);
  assert.equal(isSensitiveSignalLog(["WhatsApp connected"]), false);
});
