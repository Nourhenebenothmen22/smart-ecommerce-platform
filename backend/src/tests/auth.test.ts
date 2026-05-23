import { jest } from "@jest/globals";
import { authController } from "../controllers/auth.controller.js";
import { authService } from "../services/auth.service.js";
import { Request, Response, NextFunction } from "express";

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
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;
  let cookieMock: any;
  let clearCookieMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    cookieMock = jest.fn();
    clearCookieMock = jest.fn();
    mockRequest = {
      body: {},
    };
    mockResponse = {
      status: statusMock,
      cookie: cookieMock,
      clearCookie: clearCookieMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("register should call authService.register and set cookie", async () => {
    mockRequest.body = { email: "test@example.com", password: "password123" };
    const mockUser = { id: 1, email: "test@example.com" };
    (authService.register as any).mockResolvedValue({ user: mockUser, token: "mockToken" });

    await authController.register(mockRequest as Request, mockResponse as Response, mockNext);

    expect(authService.register).toHaveBeenCalledWith(mockRequest.body);
    expect(cookieMock).toHaveBeenCalledWith("access_token", "mockToken", expect.any(Object));
    expect(statusMock).toHaveBeenCalledWith(201); // StatusCodes.CREATED is 201
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Registration successful",
        data: { user: mockUser },
      })
    );
  });

  test("login should call authService.login and set cookie", async () => {
    mockRequest.body = { email: "test@example.com", password: "password123" };
    const mockUser = { id: 1, email: "test@example.com" };
    (authService.login as any).mockResolvedValue({ user: mockUser, token: "mockToken" });

    await authController.login(mockRequest as Request, mockResponse as Response, mockNext);

    expect(authService.login).toHaveBeenCalledWith("test@example.com", "password123");
    expect(cookieMock).toHaveBeenCalledWith("access_token", "mockToken", expect.any(Object));
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Login successful",
      })
    );
  });

  test("logout should clear cookie", async () => {
    mockRequest.user = { id: 1, role: "customer", email: "test@example.com" };
    (authService.revokeUserTokens as any).mockResolvedValue(undefined);

    await authController.logout(mockRequest as Request, mockResponse as Response, mockNext);

    expect(authService.revokeUserTokens).toHaveBeenCalledWith(1);
    expect(clearCookieMock).toHaveBeenCalledWith("access_token", expect.any(Object));
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Logged out successfully",
      })
    );
  });
});
