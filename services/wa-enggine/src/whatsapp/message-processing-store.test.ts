import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

test("durable processing store prevents duplicate execution and resumes replies", async () => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "xninetzy-processing-"));

  try {
    const { env } = await import("../config/env");
    env.WA_PROCESSING_DIR = base;
    env.WA_MESSAGE_LEASE_MS = 1_000;
    env.WA_MESSAGE_RETRY_DELAY_MS = 100;
    const store = await import("./message-processing-store");

    const first = store.claimMessage("chat", "message", 1_000);
    assert.equal(first.action, "process");
    const leased = store.claimMessage("chat", "message", 1_500);
    assert.equal(leased.action, "duplicate");

    store.markReplyReady("chat", "message", "answer", 1_600);
    const resume = store.claimMessage("chat", "message", 1_700);
    assert.equal(resume.action, "resume_reply");
    if (resume.action === "resume_reply") assert.equal(resume.reply, "answer");

    store.markMessageCompleted("chat", "message", "outbound", 1_800);
    const completed = store.claimMessage("chat", "message", 9_000);
    assert.equal(completed.action, "duplicate");
    assert.equal(store.getMessageRecord("chat", "message")?.outbound_message_id, "outbound");
  } finally {
    fs.rmSync(base, { recursive: true, force: true });
  }
});

test("failed and stale processing records can be reclaimed after their lease", async () => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "xninetzy-retry-"));

  try {
    const { env } = await import("../config/env");
    env.WA_PROCESSING_DIR = base;
    env.WA_MESSAGE_LEASE_MS = 60_000;
    env.WA_MESSAGE_RETRY_DELAY_MS = 60_000;
    const store = await import("./message-processing-store");
    store.claimMessage("retry-chat", "retry-message", 10_000);
    store.markMessageFailed("retry-chat", "retry-message", "network", 10_100);

    assert.equal(store.claimMessage("retry-chat", "retry-message", 10_150).action, "duplicate");
    const retried = store.claimMessage("retry-chat", "retry-message", 70_200);
    assert.equal(retried.action, "process");
    assert.equal(retried.record.attempts, 2);
  } finally {
    fs.rmSync(base, { recursive: true, force: true });
  }
});
