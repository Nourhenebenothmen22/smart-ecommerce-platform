import { jest } from "@jest/globals";
import { chatController } from "../controllers/chat.controller.js";
import { chatService } from "../services/chat.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../config/env.js", () => ({
  env: {
    ML_SERVICE_TOKEN: "a".repeat(32),
    ML_SERVICE_URL: "http://127.0.0.1:8000",
    ML_REQUEST_TIMEOUT_MS: 1000,
    NODE_ENV: "test",
  },
}));

jest.mock("../services/chat.service.js", () => {
  return {
    chatService: {
      sendMessage: jest.fn<any>(),
    },
  };
});

describe("ChatController Tests", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = {
      body: {},
      user: { id: 1, role: "customer", email: "test@example.com" },
    };
    mockResponse = {
      status: statusMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("returns 400 when query is missing", async () => {
    mockRequest.body = {};

    await chatController.sendMessage(mockRequest as Request, mockResponse as Response, mockNext);

    expect(statusMock).toHaveBeenCalledWith(400);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        message: "Validation failed",
      })
    );
  });

  test("returns 400 when query is empty string", async () => {
    mockRequest.body = { query: "   " };

    await chatController.sendMessage(mockRequest as Request, mockResponse as Response, mockNext);

    expect(statusMock).toHaveBeenCalledWith(400);
  });

  test("returns 400 when query exceeds 500 characters", async () => {
    mockRequest.body = { query: "x".repeat(501) };

    await chatController.sendMessage(mockRequest as Request, mockResponse as Response, mockNext);

    expect(statusMock).toHaveBeenCalledWith(400);
  });

  test("calls chatService.sendMessage and returns result on valid request", async () => {
    const mockResult = {
      query: "hello",
      response: "Hi there!",
      context_used: [{ product_id: 1, title: "Test Product" }],
      algorithm: "Hybrid_RRF",
      session_id: "abc-123",
    };
    (chatService.sendMessage as any).mockResolvedValue(mockResult);
    mockRequest.body = { query: "hello", session_id: "abc-123" };

    await chatController.sendMessage(mockRequest as Request, mockResponse as Response, mockNext);

    expect(chatService.sendMessage).toHaveBeenCalledWith(
      { query: "hello", session_id: "abc-123" },
      1
    );
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: "Message processed successfully",
        data: mockResult,
      })
    );
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("Chat service is unavailable");
    (chatService.sendMessage as any).mockRejectedValue(error);
    mockRequest.body = { query: "hello" };

    await chatController.sendMessage(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mockNext).toHaveBeenCalledWith(error);
  });
});
