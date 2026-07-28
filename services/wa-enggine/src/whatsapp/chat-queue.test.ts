import assert from "node:assert/strict";
import test from "node:test";

import { runInChatQueue } from "./chat-queue";

test("chat queue preserves order inside a chat", async () => {
  const events: string[] = [];
  let releaseFirst!: () => void;
  const waitFirst = new Promise<void>((resolve) => {
    releaseFirst = resolve;
  });

  const first = runInChatQueue("chat-a", async () => {
    events.push("first:start");
    await waitFirst;
    events.push("first:end");
  });
  const second = runInChatQueue("chat-a", async () => {
    events.push("second:start");
  });

  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(events, ["first:start"]);
  releaseFirst();
  await Promise.all([first, second]);
  assert.deepEqual(events, ["first:start", "first:end", "second:start"]);
});

test("different chats can execute concurrently", async () => {
  const events: string[] = [];
  let release!: () => void;
  const wait = new Promise<void>((resolve) => {
    release = resolve;
  });

  const blocked = runInChatQueue("chat-blocked", async () => {
    events.push("blocked:start");
    await wait;
  });
  const independent = runInChatQueue("chat-independent", async () => {
    events.push("independent:done");
  });

  await independent;
  assert.deepEqual(events, ["blocked:start", "independent:done"]);
  release();
  await blocked;
});
