import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

interface JWTPayload {
  id: number;
  role: string;
  email?: string;
}

/**
 * Authentication Middleware
 * Extracts the JWT from the 'access_token' cookie and verifies it.
 */
export const authenticate = (req: Request, _res: Response, next: NextFunction) => {
  const token = req.cookies.access_token;

  if (!token) {
    return next(new AppError("Authentication required. Please log in.", StatusCodes.UNAUTHORIZED));
  }

  try {
    const decoded = jwt.verify(token, env.JWT_SECRET) as JWTPayload;
    
    // Attach user information to the request
    req.user = {
      id: decoded.id,
      role: decoded.role,
      email: decoded.email,
    };

    next();
  } catch (error) {
    console.error("JWT Verification Error:", error);
    next(new AppError("Invalid or expired token.", StatusCodes.UNAUTHORIZED));
  }
};
