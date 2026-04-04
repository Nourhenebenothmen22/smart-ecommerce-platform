import { Request, Response, NextFunction } from 'express';

/**
 * No-op Role Authorization Middleware (Stub)
 * Pass through for now until logic is implemented.
 */
export const authorize = (..._roles: string[]) => {
  return (_req: Request, _res: Response, next: NextFunction) => {
    // TODO: Implement RBAC logic
    next();
  };
};
