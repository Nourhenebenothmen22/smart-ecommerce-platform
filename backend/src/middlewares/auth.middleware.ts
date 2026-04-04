import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { env } from '../config/env.js';

interface JWTPayload {
  id: number;
  role: string;
  email?: string;
}

/**
 * Authentication Middleware
 * Extracts the JWT from the 'access_token' cookie and verifies it.
 */
export const authenticate = (req: Request, res: Response, next: NextFunction) => {
  const token = req.cookies.access_token;

  if (!token) {
    res.status(401).json({
      success: false,
      message: 'Authentication required. Please log in.',
    });
    return;
  }

  try {
    const decoded = jwt.verify(token, env.JWT_SECRET) as JWTPayload;
    
    // Attach user information to the request
    // This allows subsequent handlers to access req.user
    req.user = {
      id: decoded.id,
      role: decoded.role,
      email: decoded.email,
    };

    next();
  } catch (error) {
    console.error('JWT Verification Error:', error);
    res.status(401).json({
      success: false,
      message: 'Invalid or expired token.',
    });
  }
};
