import React from 'react';
import { render } from 'ink';
import { App } from './App.js';

const ENTER_ALTERNATE_SCREEN = '\x1b[?1049h';
const EXIT_ALTERNATE_SCREEN = '\x1b[?1049l';
const HIDE_CURSOR = '\x1b[?25l';
const SHOW_CURSOR = '\x1b[?25h';
const RESET_STYLE = '\x1b[0m';
const SET_DEFAULT_BACKGROUND_BLACK = '\x1b]11;#000000\x07';
const SET_DEFAULT_FOREGROUND_WHITE = '\x1b]10;#f8faff\x07';
const RESET_DEFAULT_BACKGROUND = '\x1b]111\x07';
const RESET_DEFAULT_FOREGROUND = '\x1b]110\x07';
const BLACK_BACKGROUND = '\x1b[48;2;0;0;0m';
const PRIMARY_FOREGROUND = '\x1b[38;2;248;250;255m';
const CLEAR_SCREEN = '\x1b[2J\x1b[3J\x1b[H';

let terminalCleaned = false;

function applyBlackTerminalTheme(): void {
  process.stdout.write(
    SET_DEFAULT_BACKGROUND_BLACK +
    SET_DEFAULT_FOREGROUND_WHITE +
    BLACK_BACKGROUND +
    PRIMARY_FOREGROUND
  );
}

function enterTerminalMode(): void {
  process.stdout.write(
    ENTER_ALTERNATE_SCREEN +
    HIDE_CURSOR
  );
  applyBlackTerminalTheme();
  process.stdout.write(CLEAR_SCREEN);
}

function cleanupTerminal(): void {
  if (terminalCleaned) return;
  terminalCleaned = true;
  process.stdout.write(
    RESET_STYLE +
    SHOW_CURSOR +
    EXIT_ALTERNATE_SCREEN +
    RESET_DEFAULT_BACKGROUND +
    RESET_DEFAULT_FOREGROUND
  );
}

async function main(): Promise<void> {
  enterTerminalMode();

  const instance = render(
    <App />,
    {
      exitOnCtrlC: false,
      patchConsole: true
    }
  );

  const terminate = (): void => {
    instance.unmount();
    cleanupTerminal();
  };

  process.once('SIGTERM', terminate);
  process.once('SIGHUP', terminate);
  process.once('exit', cleanupTerminal);

  try {
    await instance.waitUntilExit();
  } finally {
    cleanupTerminal();
  }
}

void main().catch((error: unknown) => {
  cleanupTerminal();
  const message = error instanceof Error ? error.stack ?? error.message : String(error);
  process.stderr.write(message + '\n');
  process.exitCode = 1;
});
