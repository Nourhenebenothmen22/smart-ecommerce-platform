import { jest } from "@jest/globals";
import { mlService } from "../../services/ml.service.js";
import { chatService } from "../../services/chat.service.js";
import { pool } from "../../db/pool.js";

jest.mock("../../db/pool.js", () => ({
  pool: { query: jest.fn<any>() },
}));

jest.mock("../../config/env.js", () => ({
  env: {
    ML_SERVICE_TOKEN: "a".repeat(32),
    ML_SERVICE_URL: "http://127.0.0.1:8000",
    ML_REQUEST_TIMEOUT_MS: 2000,
    NODE_ENV: "test",
  },
}));

describe("Backend ↔ ML Integration Contract", () => {
  const fetchMock = jest.fn<any>();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = fetchMock as unknown as typeof fetch;
    (pool.query as any).mockResolvedValue({ rows: [] });
  });

  describe("ML Price Prediction", () => {
    const validPriceResponse = {
      product_id: 10,
      predicted_price: 199.99,
      currency: "EUR",
      model_name: "product_price_prediction",
      model_version: "1.0",
      model_algorithm: "random_forest_regressor",
      preprocessing_profile: "improved",
      metrics: { rmse: 12.5 },
      features_used: ["brand", "stock"],
    };

    test("sends correct request format to ML service", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: jest.fn<any>().mockResolvedValue(validPriceResponse),
      });

      await mlService.predictProductPrice({ product_id: 10, brand: "Acme", stock: 15 });

      const call = fetchMock.mock.calls[0] as [string, RequestInit];
      const url = call[0];
      const opts = call[1];
      expect(String(url)).toBe("http://127.0.0.1:8000/price/predict");
      expect(opts.method).toBe("POST");
      expect((opts.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
      expect((opts.headers as Record<string, string>)["X-ML-Service-Token"]).toBe("a".repeat(32));
      expect(JSON.parse(opts.body as string)).toEqual({ product_id: 10, brand: "Acme", stock: 15 });
    });

    test("handles ML 503 error as Backend Service Unavailable", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 503,
        text: jest.fn<any>().mockResolvedValue("Model not loaded"),
      });

      await expect(mlService.predictProductPrice({ product_id: 1 }))
        .rejects.toThrow("ML price prediction service returned an error");
    });

    test("handles ML 422 validation error", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 422,
        text: jest.fn<any>().mockResolvedValue("Invalid input"),
      });

      await expect(mlService.predictProductPrice({ product_id: -1 }))
        .rejects.toThrow("ML price prediction service returned an error");
    });

    test("handles timeout from ML service", async () => {
      const abortError = new Error("The operation was aborted");
      abortError.name = "AbortError";
      fetchMock.mockRejectedValueOnce(abortError);

      await expect(mlService.predictProductPrice({ product_id: 1 }))
        .rejects.toThrow("ML price prediction timed out");
    });

    test("handles network error from ML service", async () => {
      fetchMock.mockRejectedValueOnce(new Error("ECONNREFUSED"));

      await expect(mlService.predictProductPrice({ product_id: 1 }))
        .rejects.toThrow("ML price prediction service is unavailable");
    });

    test("records prediction result in database", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: jest.fn<any>().mockResolvedValue(validPriceResponse),
      });
      (pool.query as any).mockResolvedValue({ rows: [] });

      await mlService.predictProductPrice({ product_id: 10, brand: "Acme" });

      expect(pool.query).toHaveBeenCalledWith(
        expect.stringContaining("INSERT INTO product_price_predictions"),
        expect.arrayContaining([10, 199.99, "EUR", "product_price_prediction", "1.0"])
      );
    });
  });

  describe("Chat Service", () => {
    const validChatResponse = {
      query: "Show me phones",
      response: "Here are our phones",
      context_used: [{ product_id: 1, title: "Phone" }],
      algorithm: "Hybrid_RRF",
      session_id: "abc-123",
    };

    test("sends correct request format to ML chat endpoint", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: jest.fn<any>().mockResolvedValue(validChatResponse),
      });

      await chatService.sendMessage({ query: "Show me phones", session_id: "abc-123" }, 1);

      const call = fetchMock.mock.calls[0] as [string, RequestInit];
      const url = call[0];
      const opts = call[1];
      expect(String(url)).toBe("http://127.0.0.1:8000/chat");
      expect(opts.method).toBe("POST");
      expect((opts.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
      expect((opts.headers as Record<string, string>)["X-ML-Service-Token"]).toBe("a".repeat(32));
      expect((opts.headers as Record<string, string>)["X-ML-User-Id"]).toBe("1");
      expect(JSON.parse(opts.body as string)).toEqual({ query: "Show me phones", session_id: "abc-123" });
    });

    test("handles chat 401 from ML service", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: jest.fn<any>().mockResolvedValue("Unauthorized"),
      });

      await expect(chatService.sendMessage({ query: "Hello" }, 1))
        .rejects.toThrow("Chat service returned an error");
    });

    test("handles chat timeout", async () => {
      const abortError = new Error("The operation was aborted");
      abortError.name = "AbortError";
      fetchMock.mockRejectedValueOnce(abortError);

      await expect(chatService.sendMessage({ query: "Hello" }, 1))
        .rejects.toThrow("Chat service timed out");
    });
  });

  describe("ML Service Token Validation", () => {
    test("throws if ML_SERVICE_TOKEN is not configured", async () => {
      const { mlService: mlWithNoToken } = await import("../../services/ml.service.js");

      jest.resetModules();
      jest.doMock("../../config/env.js", () => ({
        env: {
          ML_SERVICE_TOKEN: "",
          ML_SERVICE_URL: "http://127.0.0.1:8000",
          ML_REQUEST_TIMEOUT_MS: 2000,
          NODE_ENV: "test",
        },
      }));

      const { mlService: freshMlService } = await import("../../services/ml.service.js");
      await expect(freshMlService.predictProductPrice({ product_id: 1 }))
        .rejects.toThrow("ML service token is not configured");
    });
  });
});
