import { Request, Response, NextFunction } from "express";
import crypto from "crypto";
import { logger } from "../utils/logger.js";
import { metrics } from "../utils/metrics.js";

declare global {
  namespace Express {
    interface Request {
      id: string;
      startTime: number;
    }
  }
}

export function requestIdMiddleware(req: Request, _res: Response, next: NextFunction): void {
  req.id = (req.headers["x-request-id"] as string) || crypto.randomUUID();
  req.startTime = Date.now();
  next();
}

export function requestLoggerMiddleware(req: Request, res: Response, next: NextFunction): void {
  const end = metrics.recordRequest(req);

  res.on("finish", () => {
    const duration = Date.now() - req.startTime;
    const level = res.statusCode >= 500 ? "error" : res.statusCode >= 400 ? "warn" : "info";

    logger[level]({
      reqId: req.id,
      method: req.method,
      url: req.originalUrl || req.url,
      status: res.statusCode,
      durationMs: duration,
      contentLength: res.getHeader("content-length") || 0,
      userAgent: req.headers["user-agent"] || "-",
    }, `${req.method} ${req.originalUrl || req.url} ${res.statusCode} ${duration}ms`);

    end(res.statusCode);
  });

  next();
}

export { metrics };
