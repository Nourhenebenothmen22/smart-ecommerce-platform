import pino from "pino";
import { env } from "../config/env.js";

const isDev = env.NODE_ENV !== "production";

export const logger = pino({
  level: env.NODE_ENV === "test" ? "silent" : (process.env.LOG_LEVEL || (isDev ? "debug" : "info")),
  redact: {
    paths: ["req.headers.cookie", "req.headers.authorization", "body.password", "body.token", "headers.cookie", "headers.authorization"],
    censor: "[REDACTED]",
  },
  ...(isDev
    ? {
        transport: {
          target: "pino-pretty",
          options: {
            colorize: true,
            translateTime: "SYS:HH:MM:ss.l",
            ignore: "pid,hostname",
          },
        },
      }
    : {
        formatters: {
          level: (label) => ({ level: label }),
        },
        timestamp: pino.stdTimeFunctions.isoTime,
      }),
});
