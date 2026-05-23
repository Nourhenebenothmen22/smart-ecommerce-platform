import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { AppError } from "../utils/AppError.js";
import { env } from "../config/env.js";
import { getAllowedOrigins } from "./cors.middleware.js";

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

export const csrfOriginMiddleware = (req: Request, _res: Response, next: NextFunction) => {
  if (SAFE_METHODS.has(req.method) || !req.cookies?.access_token) {
    return next();
  }

  const origin = req.headers.origin;
  const allowedOrigins = getAllowedOrigins();

  if (!origin) {
    if (env.NODE_ENV === "production") {
      return next(new AppError("Missing Origin header", StatusCodes.FORBIDDEN));
    }
    return next();
  }

  if (!allowedOrigins.includes(origin)) {
    return next(new AppError("Invalid request origin", StatusCodes.FORBIDDEN));
  }

  next();
};
