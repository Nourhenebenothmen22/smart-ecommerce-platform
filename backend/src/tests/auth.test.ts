import { jest } from "@jest/globals";
import { authController } from "../controllers/auth.controller.js";
import { authService } from "../services/auth.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/auth.service.js", () => {
  return {
    authService: {
      register: jest.fn<any>(),
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
