import { jest } from "@jest/globals";
import { Request, Response, NextFunction } from "express";
import { env } from "../config/env.js";
import { getAllowedOrigins } from "../middlewares/cors.middleware.js";
import { csrfOriginMiddleware } from "../middlewares/csrf.middleware.js";
import { authRateLimitConfig, standardRateLimitConfig } from "../middlewares/rateLimit.middleware.js";

describe("security middleware configuration", () => {
  const originalNodeEnv = env.NODE_ENV;
  const originalFrontendUrl = env.FRONTEND_URL;
  const originalCorsAllowedOrigins = env.CORS_ALLOWED_ORIGINS;

  afterEach(() => {
    (env as any).NODE_ENV = originalNodeEnv;
    (env as any).FRONTEND_URL = originalFrontendUrl;
    (env as any).CORS_ALLOWED_ORIGINS = originalCorsAllowedOrigins;
  });

  test("production CORS only uses configured origins", () => {
    (env as any).NODE_ENV = "production";
    (env as any).FRONTEND_URL = "https://shop.example.com";
    (env as any).CORS_ALLOWED_ORIGINS = "https://admin.example.com";

    expect(getAllowedOrigins()).toEqual(["https://shop.example.com", "https://admin.example.com"]);
  });

  test("auth rate limit is stricter than the global limiter", () => {
    expect(authRateLimitConfig.max).toBeLessThan(standardRateLimitConfig.max);
  });

  test("csrf origin middleware rejects cookie-auth unsafe requests from untrusted origins", () => {
    (env as any).NODE_ENV = "production";
    (env as any).FRONTEND_URL = "https://shop.example.com";
    (env as any).CORS_ALLOWED_ORIGINS = "";

    const req = {
      method: "POST",
      cookies: { access_token: "token" },
      headers: { origin: "https://evil.example.com" },
    } as unknown as Request;
    const next = jest.fn() as unknown as NextFunction;

    csrfOriginMiddleware(req, {} as Response, next);

    expect(next).toHaveBeenCalledWith(expect.objectContaining({ statusCode: 403 }));
  });

  test("csrf origin middleware allows configured origins", () => {
    (env as any).NODE_ENV = "production";
    (env as any).FRONTEND_URL = "https://shop.example.com";
    (env as any).CORS_ALLOWED_ORIGINS = "";

    const req = {
      method: "POST",
      cookies: { access_token: "token" },
      headers: { origin: "https://shop.example.com" },
    } as unknown as Request;
    const next = jest.fn() as unknown as NextFunction;

    csrfOriginMiddleware(req, {} as Response, next);

    expect(next).toHaveBeenCalledWith();
  });
});
