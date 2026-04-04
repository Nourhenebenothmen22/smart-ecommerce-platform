import cors from 'cors';

/**
 * Centralized CORS middleware.
 * Use this to configure origin, methods, headers, etc.
 */
export const corsMiddleware = cors({
  origin: '*', // Adjust as needed for production
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
});
