import { jest } from "@jest/globals";
import { chatController } from "../controllers/chat.controller.js";
import { chatService } from "../services/chat.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/chat.service.js", () => ({
  chatService: {
    sendMessage: jest.fn<any>(),
  },
}));

describe("ChatController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: { id: 1, role: "customer", email: "test@example.com" } });
    jest.clearAllMocks();
  });

  test("sendMessage returns 400 for empty query", async () => {
    ctx.mockRequest.body = { query: "" };

    await chatController.sendMessage(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

    expect(chatService.sendMessage).not.toHaveBeenCalled();
    expect(ctx.statusMock).toHaveBeenCalledWith(400);
    expect(ctx.jsonMock).toHaveBeenCalledWith(expect.objectContaining({ success: false }));
  });

  test("sendMessage returns 400 for query exceeding max length", async () => {
    ctx.mockRequest.body = { query: "a".repeat(501) };

    await chatController.sendMessage(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

    expect(chatService.sendMessage).not.toHaveBeenCalled();
    expect(ctx.statusMock).toHaveBeenCalledWith(400);
  });

  test("sendMessage calls service and returns result", async () => {
    ctx.mockRequest.body = { query: "Show me phones", session_id: "abc-123" };
    const result = { query: "Show me phones", response: "Here are phones", context_used: [], algorithm: "Hybrid_RRF", session_id: "abc-123" };
    (chatService.sendMessage as any).mockResolvedValue(result);

    await chatController.sendMessage(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

    expect(chatService.sendMessage).toHaveBeenCalledWith({ query: "Show me phones", session_id: "abc-123" }, 1);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(expect.objectContaining({ success: true, data: result }));
  });

  test("sendMessage forwards service errors", async () => {
    ctx.mockRequest.body = { query: "Hello" };
    const error = new Error("ML service unavailable");
    (chatService.sendMessage as any).mockRejectedValue(error);

    await chatController.sendMessage(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
