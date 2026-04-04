import { ErrorRequestHandler } from 'express';
import debug from 'debug';

const log = debug('app:server');

/**
 * Global error handler middleware.
 * Ensures consistent JSON responses for internal errors.
 */
export const errorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
  log(err);

  // In production, we might log to an external service and hide stack traces
  const status = err.status || 500;
  const message = err.message || 'Internal Server Error';

  res.status(status).json({
    status: 'error',
    message,
    // Add stack trace only in development
    // ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
};
