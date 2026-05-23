import { jest } from "@jest/globals";
import jwt from "jsonwebtoken";
import { Request, Response, NextFunction } from "express";
import { authenticate } from "../middlewares/auth.middleware.js";
import { pool } from "../db/pool.js";
import { env } from "../config/env.js";

jest.mock("../db/pool.js", () => {
  return {
    pool: {
      query: jest.fn<any>(),
    },
  };
});

describe("authenticate middleware", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let next: NextFunction;

  beforeEach(() => {
    jest.clearAllMocks();
    mockRequest = {
      cookies: {},
    };
    mockResponse = {};
    next = jest.fn();
  });

  test("loads current role and status from the database instead of trusting stale JWT claims", async () => {
    const token = jwt.sign(
      { id: 1, email: "user@example.com", role: "customer", tokenVersion: 2 },
      env.JWT_SECRET
    );
    mockRequest.cookies = { access_token: token };
    (pool.query as any).mockResolvedValue({
      rows: [{ id: 1, email: "user@example.com", role: "admin", is_active: true, token_version: 2 }],
    });

    await authenticate(mockRequest as Request, mockResponse as Response, next);

    expect(mockRequest.user).toEqual({ id: 1, email: "user@example.com", role: "admin" });
    expect(next).toHaveBeenCalledWith();
  });

  test("rejects deactivated users even when the JWT is otherwise valid", async () => {
    const token = jwt.sign(
      { id: 1, email: "user@example.com", role: "admin", tokenVersion: 2 },
      env.JWT_SECRET
    );
    mockRequest.cookies = { access_token: token };
    (pool.query as any).mockResolvedValue({
      rows: [{ id: 1, email: "user@example.com", role: "admin", is_active: false, token_version: 2 }],
    });

    await authenticate(mockRequest as Request, mockResponse as Response, next);

    expect(next).toHaveBeenCalledWith(expect.objectContaining({ statusCode: 403 }));
  });

  test("rejects tokens with an old token version", async () => {
    const token = jwt.sign(
      { id: 1, email: "user@example.com", role: "admin", tokenVersion: 1 },
      env.JWT_SECRET
    );
    mockRequest.cookies = { access_token: token };
    (pool.query as any).mockResolvedValue({
      rows: [{ id: 1, email: "user@example.com", role: "admin", is_active: true, token_version: 2 }],
    });

    await authenticate(mockRequest as Request, mockResponse as Response, next);

    expect(next).toHaveBeenCalledWith(expect.objectContaining({ statusCode: 401 }));
  });
});
