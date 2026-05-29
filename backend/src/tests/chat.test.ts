import { jest } from "@jest/globals";
import { chatController } from "../controllers/chat.controller.js";
import { chatService } from "../services/chat.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";
import { mockEnvModule } from "./helpers/env-mock.js";

jest.mock("../config/env.js", () => mockEnvModule());

jest.mock("../services/chat.service.js", () => {
  return {
    chatService: {
      sendMessage: jest.fn<any>(),
    },
  };
});

describe("ChatController Tests", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: { id: 1, role: "customer", email: "test@example.com" } });
    jest.clearAllMocks();
  });

  test("returns 400 when query is missing", async () => {
    ctx.mockRequest.body = {};

    await chatController.sendMessage(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.statusMock).toHaveBeenCalledWith(400);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        message: "Validation failed",
      })
    );
  });

  test("returns 400 when query is empty string", async () => {
    ctx.mockRequest.body = { query: "   " };

    await chatController.sendMessage(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.statusMock).toHaveBeenCalledWith(400);
  });

  test("returns 400 when query exceeds 500 characters", async () => {
    ctx.mockRequest.body = { query: "x".repeat(501) };

    await chatController.sendMessage(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.statusMock).toHaveBeenCalledWith(400);
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
    ctx.mockRequest.body = { query: "hello", session_id: "abc-123" };

    await chatController.sendMessage(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(chatService.sendMessage).toHaveBeenCalledWith(
      { query: "hello", session_id: "abc-123" },
      1
    );
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
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
    ctx.mockRequest.body = { query: "hello" };

    await chatController.sendMessage(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
