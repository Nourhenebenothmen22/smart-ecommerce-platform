import { jest } from "@jest/globals";
import { Request, Response, NextFunction } from "express";
import { env } from "../config/env.js";
import { getAllowedOrigins } from "../middlewares/cors.middleware.js";
import { csrfOriginMiddleware } from "../middlewares/csrf.middleware.js";
import { authRateLimitConfig, standardRateLimitConfig } from "../middlewares/rateLimit.middleware.js";
import { parseTrustProxy } from "../config/trustProxy.js";
import fs from "fs";
import path from "path";

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

  test("trust proxy parser only enables explicit safe values", () => {
    expect(parseTrustProxy("false")).toBe(false);
    expect(parseTrustProxy("0")).toBe(false);
    expect(parseTrustProxy("true")).toBe(true);
    expect(parseTrustProxy("1")).toBe(1);
  });

  test("voice webhook is mounted before global json parser", () => {
    const appSource = fs.readFileSync(path.join(process.cwd(), "src", "app.ts"), "utf-8");
    expect(appSource.indexOf('app.use("/api/voice/webhook", voiceWebhookRouter)'))
      .toBeLessThan(appSource.indexOf("app.use(express.json())"));
  });
});
