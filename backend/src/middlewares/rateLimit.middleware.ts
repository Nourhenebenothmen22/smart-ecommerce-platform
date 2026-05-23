import rateLimit from 'express-rate-limit';

export const standardRateLimitConfig = {
    windowMs: 15 * 60 * 1000,
    max: 100,
    message: {
        status: 'error',
        message: 'Too many requests from this IP, please try again after 15 minutes',
    },
    standardHeaders: true,
    legacyHeaders: false,
};

export const authRateLimitConfig = {
    windowMs: 15 * 60 * 1000,
    max: 10,
    message: {
        status: 'error',
        message: 'Too many authentication attempts, please try again after 15 minutes',
    },
    standardHeaders: true,
    legacyHeaders: false,
};

/**
 * Standard rate limiter middleware to prevent brute-force attacks and abuse.
 */
export const rateLimitMiddleware = rateLimit(standardRateLimitConfig);

export const authRateLimitMiddleware = rateLimit(authRateLimitConfig);
