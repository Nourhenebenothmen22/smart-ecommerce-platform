import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";
import { pool } from "../db/pool.js";
import { logger } from "../utils/logger.js";

interface JWTPayload {
  id: number;
  role: string;
  email?: string;
  tokenVersion?: number;
}

/**
 * Authentication Middleware
 * Extracts the JWT from the 'access_token' cookie and verifies it.
 */
export const authenticate = async (req: Request, _res: Response, next: NextFunction) => {
  const token = req.cookies.access_token;

  if (!token) {
    return next(new AppError("Authentication required. Please log in.", StatusCodes.UNAUTHORIZED));
  }

  try {
    const decoded = jwt.verify(token, env.JWT_SECRET) as JWTPayload;
    const result = await pool.query(
      "SELECT id, email, role, is_active, token_version FROM users WHERE id = $1",
      [decoded.id]
    );

    if (result.rows.length === 0) {
      return next(new AppError("Invalid or expired token.", StatusCodes.UNAUTHORIZED));
    }

    const user = result.rows[0];

    if (!user.is_active) {
      return next(new AppError("Account is deactivated", StatusCodes.FORBIDDEN));
    }

    if (decoded.tokenVersion !== user.token_version) {
      return next(new AppError("Invalid or expired token.", StatusCodes.UNAUTHORIZED));
    }
    
    // Attach current user information from the database, not stale JWT claims.
    req.user = {
      id: user.id,
      role: user.role,
      email: user.email,
    };

    next();
  } catch (error) {
    logger.warn({ err: error }, "JWT verification failed");
    next(new AppError("Invalid or expired token.", StatusCodes.UNAUTHORIZED));
  }
};
