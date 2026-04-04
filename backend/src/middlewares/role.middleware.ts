import { Request, Response, NextFunction } from "express";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

/**
 * Role-based Authorization Middleware
 * Restricts access to specific user roles.
 * 
 * @param allowedRoles List of roles permitted to access the route.
 * @returns {Function} Express middleware function.
 */
export const authorize = (...allowedRoles: string[]) => {
  return (req: Request, _res: Response, next: NextFunction) => {
    const user = req.user;

    // 1. Check if user information exists (from authenticate middleware)
    if (!user) {
      return next(new AppError("Unauthorized. Authentication required before role check.", StatusCodes.UNAUTHORIZED));
    }

    // 2. Check if user role is in the allowed list
    if (!allowedRoles.includes(user.role)) {
      return next(
        new AppError(
          `Forbidden. Your role (${user.role}) does not have permission to access this resource.`,
          StatusCodes.FORBIDDEN
        )
      );
    }

    // Access granted
    next();
  };
};
