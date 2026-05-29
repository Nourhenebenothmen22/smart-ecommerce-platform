import { jest } from "@jest/globals";
import { voiceConfirmationController } from "../controllers/voiceConfirmation.controller.js";
import { Request, Response, NextFunction } from "express";

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
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = { params: {}, body: {}, headers: {} };
    mockResponse = { status: statusMock };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  describe("initiateCall", () => {
    function makeRequest() {
      return { params: { id: "123" }, get: jest.fn<any>().mockReturnValue("localhost:5000") } as any;
    }

    test("initiates a confirmation call for an order", async () => {
      const req = makeRequest();
      mockInitiateCall.mockResolvedValue({ providerCallId: "call_abc_123" });

      await voiceConfirmationController.initiateCall(req, mockResponse as Response, mockNext);

      expect(mockInitiateCall).toHaveBeenCalledWith(123, "https://example.com");
      expect(statusMock).toHaveBeenCalledWith(200);
      expect(jsonMock).toHaveBeenCalledWith(
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

      await voiceConfirmationController.initiateCall(req, mockResponse as Response, mockNext);

      expect(mockNext).toHaveBeenCalledWith(error);
    });
  });

  describe("getContext", () => {
    test("retrieves confirmation context for an order", async () => {
      mockRequest.params = { id: "123" };
      const context = [{ id: 1, order_id: 123, call_status: "completed" }];
      mockGetConfirmationContext.mockResolvedValue(context);

      await voiceConfirmationController.getContext(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mockGetConfirmationContext).toHaveBeenCalledWith(123);
      expect(statusMock).toHaveBeenCalledWith(200);
      expect(jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({ success: true, data: context })
      );
    });

    test("forwards errors to next handler", async () => {
      mockRequest.params = { id: "123" };
      const error = new Error("Context error");
      mockGetConfirmationContext.mockRejectedValue(error);

      await voiceConfirmationController.getContext(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mockNext).toHaveBeenCalledWith(error);
    });
  });

  describe("webhook", () => {
    test("processes valid webhook payload", async () => {
      mockRequest.body = Buffer.from(JSON.stringify({ call_id: "call_1" }));
      mockRequest.headers = { "x-retell-signature": "valid-sig" };
      mockHandleWebhookResult.mockResolvedValue({ orderId: 123, outcome: "confirmed" });

      await voiceConfirmationController.webhook(mockRequest as any as Request, mockResponse as Response, mockNext);

      expect(mockHandleWebhookResult).toHaveBeenCalledWith(
        expect.any(Buffer),
        "valid-sig"
      );
      expect(statusMock).toHaveBeenCalledWith(200);
    });

    test("ignores unknown payloads gracefully", async () => {
      mockRequest.body = Buffer.from("{}");
      mockRequest.headers = { "x-retell-signature": "bad-sig" };
      mockHandleWebhookResult.mockResolvedValue(null);

      await voiceConfirmationController.webhook(mockRequest as any as Request, mockResponse as Response, mockNext);

      expect(statusMock).toHaveBeenCalledWith(200);
      expect(jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({ message: "Ignored (unknown or invalid payload)" })
      );
    });

    test("throws on missing raw body", async () => {
      mockRequest.body = "not-a-buffer";

      await voiceConfirmationController.webhook(mockRequest as any as Request, mockResponse as Response, mockNext);

      expect(mockNext).toHaveBeenCalledWith(
        expect.objectContaining({ statusCode: 400 })
      );
    });

    test("forwards errors to next handler", async () => {
      mockRequest.body = Buffer.from("{}");
      mockRequest.headers = { "x-retell-signature": "sig" };
      const error = new Error("Webhook processing error");
      mockHandleWebhookResult.mockRejectedValue(error);

      await voiceConfirmationController.webhook(mockRequest as any as Request, mockResponse as Response, mockNext);

      expect(mockNext).toHaveBeenCalledWith(error);
    });
  });
});
