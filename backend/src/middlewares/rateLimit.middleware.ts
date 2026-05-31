import rateLimit from 'express-rate-limit';
import type { Request } from 'express';

const skipInternalPaths = (req: Request) =>
    req.path.startsWith('/api/health') ||
    req.path.startsWith('/api/observability') ||
    req.path.startsWith('/api/voice/webhook');

export const standardRateLimitConfig = {
    windowMs: 15 * 60 * 1000,
    max: 300,
    message: {
        status: 'error',
        message: 'Too many requests from this IP, please try again after 15 minutes',
    },
    standardHeaders: true,
    legacyHeaders: false,
    skip: skipInternalPaths,
};

export const authLoginRateLimitConfig = {
    windowMs: 15 * 60 * 1000,
    max: 10,
    message: {
        status: 'error',
        message: 'Too many login attempts, please try again after 15 minutes',
    },
    standardHeaders: true,
    legacyHeaders: false,
};

export const authRegisterRateLimitConfig = {
    windowMs: 15 * 60 * 1000,
    max: 5,
    message: {
        status: 'error',
        message: 'Too many registration attempts, please try again after 15 minutes',
    },
    standardHeaders: true,
    legacyHeaders: false,
};

export const rateLimitMiddleware = rateLimit(standardRateLimitConfig);
export const authLoginRateLimitMiddleware = rateLimit(authLoginRateLimitConfig);
export const authRegisterRateLimitMiddleware = rateLimit(authRegisterRateLimitConfig);
