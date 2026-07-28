import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

test("durable media manifest survives an empty message cache", async () => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "xninetzy-media-"));
  process.env.WA_MEDIA_DIR = base;
  const directory = path.join(base, "chat", "message");
  fs.mkdirSync(directory, { recursive: true });
  const localPath = path.join(directory, "note.txt");
  fs.writeFileSync(localPath, "hello");
  fs.writeFileSync(
    path.join(directory, "_media.json"),
    JSON.stringify({
      local_path: localPath,
      filename: "note.txt",
      mime_type: "text/plain",
      media_type: "document",
      size_bytes: 5,
      sha256: "diagnostic",
    }),
  );

  try {
    const { getStoredMedia, getStoredMediaContent } = await import("./durable-media");
    const stored = getStoredMedia("chat", "message");
    assert.equal(stored?.filename, "note.txt");
    assert.equal(stored?.size_bytes, 5);
    const content = getStoredMediaContent("chat", "message");
    assert.equal(content?.content_base64, Buffer.from("hello").toString("base64"));
  } finally {
    fs.rmSync(base, { recursive: true, force: true });
  }
});
