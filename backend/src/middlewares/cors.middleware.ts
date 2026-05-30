import cors from 'cors';
import { env } from '../config/env.js';

export const getAllowedOrigins = () => {
  const configuredOrigins = env.CORS_ALLOWED_ORIGINS
    ?.split(",")
    .map((origin) => origin.trim())
    .filter(Boolean) ?? [];

  const origins = new Set([env.FRONTEND_URL, ...configuredOrigins]);

  if (env.NODE_ENV !== "production") {
    origins.add("http://localhost:5173");
    origins.add("http://localhost:3000");
    origins.add("http://localhost:5000");
  }

  return [...origins];
};

/**
 * Centralized CORS middleware.
 * Configured for React frontend (Vite/CRA) support.
 */
export const corsMiddleware = cors({
  origin: getAllowedOrigins(),
  credentials: true, // Required for cookies/session handling in React
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept'],
});
