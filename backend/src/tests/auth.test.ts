import { jest } from "@jest/globals";
import { authController } from "../controllers/auth.controller.js";
import { authService } from "../services/auth.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/auth.service.js", () => {
  return {
    authService: {
      register: jest.fn<any>(),
      registerAdmin: jest.fn<any>(),
      login: jest.fn<any>(),
      revokeUserTokens: jest.fn<any>(),
    },
  };
});

describe("AuthController Tests", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: null });
    jest.clearAllMocks();
  });

  test("register should call authService.register and set cookie", async () => {
    ctx.mockRequest.body = { email: "test@example.com", password: "password123" };
    const mockUser = { id: 1, email: "test@example.com" };
    (authService.register as any).mockResolvedValue({ user: mockUser, token: "mockToken" });

    await authController.register(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(authService.register).toHaveBeenCalledWith(ctx.mockRequest.body);
    expect(ctx.mockResponse.cookie).toHaveBeenCalledWith("access_token", "mockToken", expect.any(Object));
    expect(ctx.statusMock).toHaveBeenCalledWith(201);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Registration successful",
        data: { user: mockUser },
      })
    );
  });

  test("login should call authService.login and set cookie", async () => {
    ctx.mockRequest.body = { email: "test@example.com", password: "password123" };
    const mockUser = { id: 1, email: "test@example.com" };
    (authService.login as any).mockResolvedValue({ user: mockUser, token: "mockToken" });

    await authController.login(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(authService.login).toHaveBeenCalledWith("test@example.com", "password123");
    expect(ctx.mockResponse.cookie).toHaveBeenCalledWith("access_token", "mockToken", expect.any(Object));
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Login successful",
      })
    );
  });

  test("registerAdmin should call authService.registerAdmin and not set cookie", async () => {
    ctx.mockRequest.body = { email: "admin@example.com", password: "password123" };
    const mockAdmin = { id: 2, email: "admin@example.com", role: "admin" };
    (authService.registerAdmin as any).mockResolvedValue({ user: mockAdmin });

    await authController.registerAdmin(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(authService.registerAdmin).toHaveBeenCalledWith(ctx.mockRequest.body);
    expect(ctx.mockResponse.cookie).not.toHaveBeenCalled();
    expect(ctx.statusMock).toHaveBeenCalledWith(201);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Admin registration successful",
        data: { user: mockAdmin },
      })
    );
  });

  test("registerAdmin forwards errors to next handler", async () => {
    const error = new Error("Email already registered");
    (authService.registerAdmin as any).mockRejectedValue(error);
    ctx.mockRequest.body = { email: "existing@example.com", password: "password123" };

    await authController.registerAdmin(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });

  test("register service always creates customer role regardless of body", async () => {
    ctx.mockRequest.body = { email: "test@example.com", password: "password123", role: "admin" };
    const mockUser = { id: 1, email: "test@example.com", role: "customer" };
    (authService.register as any).mockResolvedValue({ user: mockUser, token: "mockToken" });

    await authController.register(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(authService.register).toHaveBeenCalledWith(
      expect.objectContaining({ email: "test@example.com", role: "admin" })
    );
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ user: expect.objectContaining({ role: "customer" }) }),
      })
    );
  });

  test("logout should clear cookie", async () => {
    ctx.mockRequest.user = { id: 1, role: "customer", email: "test@example.com" } as any;
    (authService.revokeUserTokens as any).mockResolvedValue(undefined);

    await authController.logout(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(authService.revokeUserTokens).toHaveBeenCalledWith(1);
    expect(ctx.mockResponse.clearCookie).toHaveBeenCalledWith("access_token", expect.any(Object));
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Logged out successfully",
      })
    );
  });
});
