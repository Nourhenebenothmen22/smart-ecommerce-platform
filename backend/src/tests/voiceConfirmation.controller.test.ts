import { jest } from "@jest/globals";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

// Mock providers BEFORE importing the controller
const mockDispatch = jest.fn<any>();
const mockParseWebhook = jest.fn<any>();
const mockInitiateCall = jest.fn<any>();
const mockHandleWebhook = jest.fn<any>();
const mockGetContext = jest.fn<any>();

jest.mock("../services/voice/retell.provider.js", () => ({
  RetellProvider: jest.fn().mockImplementation(() => ({
    name: "retell",
    dispatch: mockDispatch,
    parseWebhook: mockParseWebhook,
  })),
}));

jest.mock("../services/phoneConfirmation.service.js", () => ({
  PhoneConfirmationService: jest.fn().mockImplementation(() => ({
    initiateCall: mockInitiateCall,
    handleWebhookResult: mockHandleWebhook,
    getConfirmationContext: mockGetContext,
  })),
}));

import { voiceConfirmationController } from "../controllers/voiceConfirmation.controller.js";

beforeEach(() => {
  jest.clearAllMocks();
});

describe("VoiceConfirmationController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: { id: 1, role: "admin", email: "admin@example.com" } });
  });

  describe("webhook", () => {
    test("returns 400 if req.body is not a Buffer", async () => {
      ctx.mockRequest.body = { some: "json" };

      await voiceConfirmationController.webhook(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(ctx.mockNext).toHaveBeenCalledWith(
        expect.objectContaining({ statusCode: 400 })
      );
    });

    test("processes valid webhook payload", async () => {
      const rawBody = Buffer.from(JSON.stringify({ call_id: "call-123" }));
      ctx.mockRequest.body = rawBody;
      ctx.mockRequest.headers = { "x-retell-signature": "valid-sig" } as any;
      mockHandleWebhook.mockResolvedValue({ orderId: 42, outcome: "confirmed" });

      await voiceConfirmationController.webhook(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(mockHandleWebhook).toHaveBeenCalledWith(rawBody, "valid-sig");
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });
  });

  describe("initiateCall", () => {
    test("initiates call for valid order", async () => {
      ctx.mockRequest.params = { id: "42" };
      ctx.mockRequest.headers = { host: "localhost:5000" } as any;
      ctx.mockRequest.get = jest.fn<any>().mockImplementation((name: string) => {
        if (name === "host") return "localhost:5000";
        return undefined;
      });
      Object.defineProperty(ctx.mockRequest, "protocol", { value: "http", writable: false });
      mockInitiateCall.mockResolvedValue({ providerCallId: "call-789" });

      await voiceConfirmationController.initiateCall(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(mockInitiateCall).toHaveBeenCalledWith(42, expect.stringContaining("localhost"));
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });
  });

  describe("getContext", () => {
    test("returns confirmation context", async () => {
      ctx.mockRequest.params = { id: "42" };
      const context = [{ id: 1, order_id: 42, call_status: "completed" }];
      mockGetContext.mockResolvedValue(context);

      await voiceConfirmationController.getContext(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(mockGetContext).toHaveBeenCalledWith(42);
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });
  });
});
