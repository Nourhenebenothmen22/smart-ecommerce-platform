import { jest } from "@jest/globals";
import { voiceConfirmationController } from "../controllers/voiceConfirmation.controller.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

const mockInitiateCall = jest.fn<any>();
const mockHandleWebhookResult = jest.fn<any>();
const mockGetConfirmationContext = jest.fn<any>();

jest.mock("../services/phoneConfirmation.service.js", () => ({
  PhoneConfirmationService: jest.fn().mockImplementation(() => ({
    initiateCall: mockInitiateCall,
    handleWebhookResult: mockHandleWebhookResult,
    getConfirmationContext: mockGetConfirmationContext,
  })),
}));

jest.mock("../services/voice/retell.provider.js", () => ({
  RetellProvider: jest.fn().mockImplementation(() => ({
    name: "mock-provider",
    dispatch: jest.fn<any>(),
    parseWebhook: jest.fn<any>(),
  })),
}));

jest.mock("../config/env.js", () => ({
  env: {
    WEBHOOK_BASE_URL: "https://example.com",
    NODE_ENV: "test",
    RETELL_API_KEY: "test-key",
    RETELL_AGENT_ID: "agent-123",
    RETELL_FROM_NUMBER: "+15551234567",
    RETELL_WEBHOOK_SECRET: "webhook-secret",
  },
}));

describe("VoiceConfirmationController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: null });
    jest.clearAllMocks();
  });

  describe("initiateCall", () => {
    function makeRequest() {
      return { params: { id: "123" }, get: jest.fn<any>().mockReturnValue("localhost:5000") } as any;
    }

    test("initiates a confirmation call for an order", async () => {
      const req = makeRequest();
      mockInitiateCall.mockResolvedValue({ providerCallId: "call_abc_123" });

      await voiceConfirmationController.initiateCall(req, ctx.mockResponse as Response, ctx.mockNext);

      expect(mockInitiateCall).toHaveBeenCalledWith(123, "https://example.com");
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
      expect(ctx.jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({
          success: true,
          data: expect.objectContaining({ orderId: 123, providerCallId: "call_abc_123" }),
        })
      );
    });

    test("forwards errors to next handler", async () => {
      const req = makeRequest();
      const error = new Error("Call failed");
      mockInitiateCall.mockRejectedValue(error);

      await voiceConfirmationController.initiateCall(req, ctx.mockResponse as Response, ctx.mockNext);

      expect(ctx.mockNext).toHaveBeenCalledWith(error);
    });
  });

  describe("getContext", () => {
    test("retrieves confirmation context for an order", async () => {
      ctx.mockRequest.params = { id: "123" };
      const context = [{ id: 1, order_id: 123, call_status: "completed" }];
      mockGetConfirmationContext.mockResolvedValue(context);

      await voiceConfirmationController.getContext(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mockGetConfirmationContext).toHaveBeenCalledWith(123);
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
      expect(ctx.jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({ success: true, data: context })
      );
    });

    test("forwards errors to next handler", async () => {
      ctx.mockRequest.params = { id: "123" };
      const error = new Error("Context error");
      mockGetConfirmationContext.mockRejectedValue(error);

      await voiceConfirmationController.getContext(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(ctx.mockNext).toHaveBeenCalledWith(error);
    });
  });

  describe("webhook", () => {
    test("processes valid webhook payload", async () => {
      ctx.mockRequest.body = Buffer.from(JSON.stringify({ call_id: "call_1" }));
      ctx.mockRequest.headers = { "x-retell-signature": "valid-sig" };
      mockHandleWebhookResult.mockResolvedValue({ orderId: 123, outcome: "confirmed" });

      await voiceConfirmationController.webhook(
        ctx.mockRequest as any as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mockHandleWebhookResult).toHaveBeenCalledWith(
        expect.any(Buffer),
        "valid-sig"
      );
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });

    test("ignores unknown payloads gracefully", async () => {
      ctx.mockRequest.body = Buffer.from("{}");
      ctx.mockRequest.headers = { "x-retell-signature": "bad-sig" };
      mockHandleWebhookResult.mockResolvedValue(null);

      await voiceConfirmationController.webhook(
        ctx.mockRequest as any as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(ctx.statusMock).toHaveBeenCalledWith(200);
      expect(ctx.jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({ message: "Ignored (unknown or invalid payload)" })
      );
    });

    test("throws on missing raw body", async () => {
      ctx.mockRequest.body = "not-a-buffer";

      await voiceConfirmationController.webhook(
        ctx.mockRequest as any as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(ctx.mockNext).toHaveBeenCalledWith(
        expect.objectContaining({ statusCode: 400 })
      );
    });

    test("forwards errors to next handler", async () => {
      ctx.mockRequest.body = Buffer.from("{}");
      ctx.mockRequest.headers = { "x-retell-signature": "sig" };
      const error = new Error("Webhook processing error");
      mockHandleWebhookResult.mockRejectedValue(error);

      await voiceConfirmationController.webhook(
        ctx.mockRequest as any as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(ctx.mockNext).toHaveBeenCalledWith(error);
    });
  });
});
