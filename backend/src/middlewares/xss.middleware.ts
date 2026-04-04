import DOMPurify from 'dompurify';
import { JSDOM } from 'jsdom';
import { Request, Response, NextFunction } from 'express';

const window = new JSDOM('').window;
const purify = DOMPurify(window as any);

/**
 * Middleware to sanitize user input in req.body to prevent XSS attacks.
 * It recursively cleans strings in the body object.
 */
export const xssMiddleware = (req: Request, _res: Response, next: NextFunction) => {
  if (req.body) {
    req.body = sanitizeObject(req.body);
  }
  next();
};

function sanitizeObject(obj: any): any {
  for (const key in obj) {
    if (typeof obj[key] === 'string') {
      obj[key] = purify.sanitize(obj[key]);
    } else if (typeof obj[key] === 'object' && obj[key] !== null) {
      obj[key] = sanitizeObject(obj[key]);
    }
  }
  return obj;
}
