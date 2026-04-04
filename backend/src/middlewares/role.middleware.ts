import { Request, Response, NextFunction } from 'express';

/**
 * Role-based Authorization Middleware
 * Restricts access to specific user roles.
 * 
 * @param allowedRoles List of roles permitted to access the route.
 * @returns {Function} Express middleware function.
 */
export const authorize = (...allowedRoles: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;

    // 1. Check if user information exists (from authenticate middleware)
    if (!user) {
      res.status(401).json({
        success: false,
        message: 'Unauthorized. Authentication required before role check.',
      });
      return;
    }

    // 2. Check if user role is in the allowed list
    if (!allowedRoles.includes(user.role)) {
      res.status(403).json({
        success: false,
        message: `Forbidden. Your role (${user.role}) does not have permission to access this resource.`,
      });
      return;
    }

    // Access granted
    next();
  };
};
