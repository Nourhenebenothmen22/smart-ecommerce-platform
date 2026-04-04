import cors from 'cors';
import { env } from '../config/env.js';

/**
 * Centralized CORS middleware.
 * Configured for React frontend (Vite/CRA) support.
 */
export const corsMiddleware = cors({
  origin: [env.FRONTEND_URL, 'http://localhost:5173', 'http://localhost:3000'], // Vite, CRA, and Environment defined URL
  credentials: true, // Required for cookies/session handling in React
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept'],
  exposedHeaders: ['set-cookie'], // Expose specific headers to the frontend if needed
});
