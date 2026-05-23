import { jest } from "@jest/globals";
import { PhoneConfirmationService } from "../services/phoneConfirmation.service.js";
import { IVoiceProvider, CallContext, DispatchResult, WebhookResult } from "../services/voice/voiceProvider.adapter.js";
import { pool } from "../db/pool.js";
import { orderService } from "../services/order.service.js";
import { AppError } from "../utils/AppError.js";

// Mock the PG pool
jest.mock("../db/pool.js", () => {
  const mockClient = {
    query: jest.fn(),
    release: jest.fn(),
  };
  return {
    pool: {
      connect: jest.fn<any>().mockResolvedValue(mockClient as any),
      query: jest.fn(),
    },
  };
});

// Mock the OrderService
jest.mock("../services/order.service.js", () => {
  return {
    orderService: {
      updateStatus: jest.fn<any>().mockResolvedValue({} as any),
      createOrder: jest.fn(),
    },
  };
});

describe("Phone Confirmation Service Tests", () => {
  let mockProvider: jest.Mocked<IVoiceProvider>;
  let service: PhoneConfirmationService;
  let mockClient: any;

  beforeEach(async () => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockClient = await pool.connect();

    mockProvider = {
      name: "mock-provider",
      dispatch: jest.fn<any>(),
      parseWebhook: jest.fn<any>(),
    } as any;

    service = new PhoneConfirmationService(mockProvider);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  // 1. Phone Call Triggered & Success Flow
  test("should trigger phone call and return provider call id for a valid order", async () => {
    // Mock database responses
    mockClient.query
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({
        rows: [
          {
            id: 123,
            user_id: 456,
            total_amount: "150.00",
            status: "pending_phone_confirmation",
            payment_status: "pending",
          },
        ],
      }) // Select order
      .mockResolvedValueOnce({ rows: [] }) // Select active call (none)
      .mockResolvedValueOnce({
        rows: [
          {
            id: 456,
            first_name: "John",
            last_name: "Doe",
            phone: "+15551234567",
            address_line: "123 Main St",
            city: "Springfield",
            postal_code: "12345",
            country: "USA",
          },
        ],
      }) // Select user
      .mockResolvedValueOnce({
        rows: [
          {
            product_name_snapshot: "Cool Widget",
            quantity: 2,
            unit_price: "75.00",
          },
        ],
      }) // Select items
      .mockResolvedValueOnce({
        rows: [
          {
            payment_method: "credit_card",
            status: "pending",
          },
        ],
      }) // Select payment info
      .mockResolvedValueOnce({ rows: [] }) // Insert voice_confirmation
      .mockResolvedValueOnce({ rows: [] }); // COMMIT

    mockProvider.dispatch.mockResolvedValue({ providerCallId: "call_abc_123" });

    const result = await service.initiateCall(123, "https://example.com");

    expect(result.providerCallId).toBe("call_abc_123");
    expect(mockProvider.dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        orderId: 123,
        customerName: "John Doe",
        phone: "+15551234567",
        itemsSummary: "2× Cool Widget",
        totalAmount: "$150.00",
      })
    );
  });

  // 2. Missing Phone Number Blocks Call
  test("should throw error if user phone number is missing or invalid", async () => {
    mockClient.query
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({
        rows: [
          {
            id: 123,
            user_id: 456,
            total_amount: "150.00",
            status: "pending_phone_confirmation",
            payment_status: "pending",
          },
        ],
      }) // Select order
      .mockResolvedValueOnce({ rows: [] }) // Select active call (none)
      .mockResolvedValueOnce({
        rows: [
          {
            id: 456,
            first_name: "John",
            last_name: "Doe",
            phone: null, // missing phone
          },
        ],
      }); // Select user

    await expect(service.initiateCall(123, "https://example.com")).rejects.toThrow(
      "User has no valid phone number on file. Phone confirmation cannot proceed."
    );
  });

  // 3. Duplicate Call is Blocked
  test("should throw error if a call is already in progress for the order", async () => {
    mockClient.query
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({
        rows: [
          {
            id: 123,
            user_id: 456,
            total_amount: "150.00",
            status: "pending_phone_confirmation",
            payment_status: "pending",
          },
        ],
      }) // Select order
      .mockResolvedValueOnce({
        rows: [{ id: 999 }], // Active call exists
      }); // Select active call

    await expect(service.initiateCall(123, "https://example.com")).rejects.toThrow(
      "A call for order 123 is already in progress."
    );
  });

  // 4. Webhook: Confirmed call updates order to processing
  test("should update order status to processing when call is confirmed", async () => {
    mockProvider.parseWebhook.mockReturnValue({
      providerCallId: "call_abc_123",
      outcome: "confirmed",
      transcript: "Yes, I confirm the order.",
    });

    mockClient.query
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({
        rows: [{ id: 1, order_id: 123, retry_count: 0 }],
      }) // Find voice_confirmation
      .mockResolvedValueOnce({ rows: [] }) // Update voice_confirmation
      .mockResolvedValueOnce({ rows: [] }); // COMMIT

    await service.handleWebhookResult(Buffer.from("{}"), "sig");

    expect(orderService.updateStatus).toHaveBeenCalledWith(123, "processing", mockClient);
  });

  // 5. Webhook: Cancelled call updates order to cancelled
  test("should update order status to cancelled when user cancels", async () => {
    mockProvider.parseWebhook.mockReturnValue({
      providerCallId: "call_abc_123",
      outcome: "cancelled",
      transcript: "No, please cancel it.",
    });

    mockClient.query
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({
        rows: [{ id: 1, order_id: 123, retry_count: 0 }],
      }) // Find voice_confirmation
      .mockResolvedValueOnce({ rows: [] }) // Update voice_confirmation
      .mockResolvedValueOnce({ rows: [] }); // COMMIT

    await service.handleWebhookResult(Buffer.from("{}"), "sig");

    expect(orderService.updateStatus).toHaveBeenCalledWith(123, "cancelled", mockClient);
  });

  // 6. Webhook: No Answer keeps order pending
  test("should keep order pending when call result is no_answer", async () => {
    mockProvider.parseWebhook.mockReturnValue({
      providerCallId: "call_abc_123",
      outcome: "no_answer",
    });

    mockClient.query
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({
        rows: [{ id: 1, order_id: 123, retry_count: 0 }],
      }) // Find voice_confirmation
      .mockResolvedValueOnce({ rows: [] }) // Update voice_confirmation
      .mockResolvedValueOnce({ rows: [] }); // COMMIT

    await service.handleWebhookResult(Buffer.from("{}"), "sig");

    // Order status update should NOT be called
    expect(orderService.updateStatus).not.toHaveBeenCalled();
  });

  // 7. Webhook: Unclear response sends order to manual_review
  test("should set order to manual_review when call result is unclear", async () => {
    mockProvider.parseWebhook.mockReturnValue({
      providerCallId: "call_abc_123",
      outcome: "unclear",
      transcript: "Maybe, I am not sure.",
    });

    mockClient.query
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({
        rows: [{ id: 1, order_id: 123, retry_count: 0 }],
      }) // Find voice_confirmation
      .mockResolvedValueOnce({ rows: [] }) // Update voice_confirmation
      .mockResolvedValueOnce({ rows: [] }); // COMMIT

    await service.handleWebhookResult(Buffer.from("{}"), "sig");

    expect(orderService.updateStatus).toHaveBeenCalledWith(123, "manual_review", mockClient);
  });
});
