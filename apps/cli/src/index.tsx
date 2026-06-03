import React from 'react';
import { render } from 'ink';
import { execSync } from 'node:child_process';
import { App } from './app.js';
import { getMockReply } from './mock.js';

async function runPipedInput() {
  let buffer = '';

  process.stdin.setEncoding('utf8');
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
  // Clear screen, move cursor to home, set background black, foreground white
  process.stdout.write('\x1b[2J\x1b[3J\x1b[H\x1b[40m\x1b[37m');
  
  const { waitUntilExit } = render(<App />);
  
  await waitUntilExit();

  // Full terminal reset command
  try {
    execSync('reset', { stdio: 'inherit' });
  } catch {
    // Fallback to ANSI reset if 'reset' command fails
    process.stdout.write('\x1bc');
  }

  // Closing message following the style
  process.stdout.write('\x1b[38;5;135mX N I N E T Z Y\x1b[0m\n');
  process.stdout.write('\x1b[38;5;214m◎ event horizon detached\x1b[0m\n\n');
  process.stdout.write('\x1b[37mready for making a .., continue session ...\x1b[0m\n');
  process.stdout.write('\x1b[38;5;63m✦ drifting through your second brain space ✦\x1b[0m\n\n');
} else {
  await runPipedInput();
}
