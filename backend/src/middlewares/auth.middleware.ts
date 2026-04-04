import { Request, Response, NextFunction } from 'express';

/**
 * No-op Authentication Middleware (Stub)
 * Pass through for now until logic is implemented.
 */
export const authenticate = (req: Request, _res: Response, next: NextFunction) => {
  // TODO: Implement JWT verification logic
  // For now, attaching a mock user to the request
  (req as any).user = { id: 1, role: 'admin' };
  next();
};
