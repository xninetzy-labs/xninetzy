import pino from "pino";

export const logger = pino({
  level: process.env.WA_LOG_LEVEL ?? process.env.LOG_LEVEL ?? "info",
});
