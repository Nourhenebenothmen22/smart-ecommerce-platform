import { jest, beforeAll, describe, test, expect } from "@jest/globals";

jest.unstable_mockModule("../../config/env.js", () => ({
  env: {
    PORT: 0,
    HOST: "127.0.0.1",
    DATABASE_URL: "postgresql://test:test@localhost:5432/test",
    JWT_SECRET: "test-jwt-secret-12345678901234567890",
    JWT_EXPIRES_IN: "15m",
    NODE_ENV: "test",
    FRONTEND_URL: "http://localhost:5173",
    CORS_ALLOWED_ORIGINS: undefined,
    WEBHOOK_BASE_URL: undefined,
    RETELL_API_KEY: undefined,
    RETELL_AGENT_ID: undefined,
    RETELL_FROM_NUMBER: undefined,
    RETELL_WEBHOOK_SECRET: undefined,
    ML_SERVICE_TOKEN: undefined,
    ML_SERVICE_URL: "http://127.0.0.1:8000",
    ML_REQUEST_TIMEOUT_MS: 5000,
    TRUST_PROXY: "false",
    COOKIE_SECRET: undefined,
  },
}));

jest.unstable_mockModule("../../db/pool.js", () => ({
  pool: { query: jest.fn(), connect: jest.fn() },
}));

jest.unstable_mockModule("../../utils/logger.js", () => ({
  logger: {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn(),
  },
}));

const { default: request } = await import("supertest");
const { app } = await import("../../app.js");

describe("GET /api/health", () => {
  test("returns 200 with success status", async () => {
    const res = await request(app).get("/api/health");

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      status: "success",
      message: "Server is healthy",
    });
    expect(res.body).toHaveProperty("timestamp");
  });
});

describe("GET /api/docs.json", () => {
  test("returns OpenAPI spec", async () => {
    const res = await request(app).get("/api/docs.json");

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty("openapi", "3.0.0");
    expect(res.body).toHaveProperty("info");
    expect(res.body).toHaveProperty("paths");
  });
});

describe("404 handler", () => {
  test("returns 404 for unknown routes", async () => {
    const res = await request(app).get("/api/nonexistent");

    expect(res.status).toBe(404);
    expect(res.body).toMatchObject({
      success: false,
      message: "Route not found",
    });
  });
});
