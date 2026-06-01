import React from "react";
import { render } from "ink";
import { App } from "./app.js";
import { getMockReply } from "./mock.js";

async function runPipedInput() {
  let buffer = "";

  process.stdin.setEncoding("utf8");
  for await (const chunk of process.stdin) {
    buffer += chunk;
  }

  const lines = buffer
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  for (const line of lines) {
    process.stdout.write(`You\n${line}\n\n`);
    process.stdout.write(`Xninetzy\n${getMockReply(line)}\n`);
  }
}

if (process.stdin.isTTY) {
  render(<App />);
} else {
  await runPipedInput();
}
