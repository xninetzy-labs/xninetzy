import { logger } from "./logger";

const SIGNAL_LOG_PREFIXES = new Set([
  "Closing session:",
  "Session already closed",
]);

export function isSensitiveSignalLog(args: unknown[]): boolean {
  return typeof args[0] === "string" && SIGNAL_LOG_PREFIXES.has(args[0]);
}

export function installConsoleRedaction(): void {
  const info = console.info.bind(console);
  const warn = console.warn.bind(console);
  console.info = (...args: unknown[]) => {
    if (isSensitiveSignalLog(args)) {
      logger.debug({ step: "signal_session_rotated" }, "Signal session rotated");
      return;
    }
    info(...args);
  };
  console.warn = (...args: unknown[]) => {
    if (isSensitiveSignalLog(args)) {
      logger.debug({ step: "signal_session_state_skipped" }, "Signal session state skipped");
      return;
    }
    warn(...args);
  };
}
