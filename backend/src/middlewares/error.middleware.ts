import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { env } from "../config/env.js";
import { ZodError } from "zod";
import { logger } from "../utils/logger.js";

/**
 * Global error handling middleware.
 * Formats errors into a consistent JSON response.
 */
export const errorHandler = (
  err: any,
  req: Request,
  res: Response,
  _next: NextFunction
): void => {
  logger.error({
    reqId: req.id,
    err,
    method: req.method,
    url: req.originalUrl || req.url,
  }, err.stack || err.message);

  let statusCode = err.status || err.statusCode || StatusCodes.INTERNAL_SERVER_ERROR;
  let message = err.message || "An unexpected error occurred on the server";
  let errors: any = undefined;

  // Handle Zod Validation Errors
  if (err instanceof ZodError) {
    statusCode = StatusCodes.BAD_REQUEST;
    message = "Validation failed";
    errors = err.flatten().fieldErrors;
  }

  // Handle JWT Errors
  if (err.name === "UnauthorizedError" || err.name === "JsonWebTokenError") {
    statusCode = StatusCodes.UNAUTHORIZED;
    message = "Invalid or expired token";
  }

  if (err.name === "TokenExpiredError") {
    statusCode = StatusCodes.UNAUTHORIZED;
    message = "Token has expired";
  }

  // Handle DB Unique Constraint Violations (Postgres)
  if (err.code === "23505") {
    statusCode = StatusCodes.CONFLICT;
    message = "Resource already exists";
  }

  res.status(statusCode).json({
    success: false,
    message,
    errors,
    stack: env.NODE_ENV === "development" ? err.stack : undefined,
  });
};
