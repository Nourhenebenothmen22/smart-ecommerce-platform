import { Request, Response, NextFunction } from 'express';
import { StatusCodes } from 'http-status-codes';
import debug from 'debug';

const logError = debug('app:error');

/**
 * Global error handling middleware.
 * Formats errors into a consistent JSON response.
 */
export const errorHandler = (
    err: any,
    _req: Request,
    res: Response,
    _next: NextFunction
) => {
    logError(err.stack || err.message);

    const statusCode = err.status || err.statusCode || StatusCodes.INTERNAL_SERVER_ERROR;
    const message = err.message || 'An unexpected error occurred on the server';

    res.status(statusCode).json({
        success: false,
        message,
        // Only show stack trace in development mode for easier debugging
        stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    });
};
