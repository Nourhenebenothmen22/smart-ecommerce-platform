import { jest } from "@jest/globals";
import { mlService } from "../services/ml.service.js";
import { pool } from "../db/pool.js";

jest.mock("../config/env.js", () => ({
  env: {
    ML_SERVICE_TOKEN: "a".repeat(32),
    ML_SERVICE_URL: "http://127.0.0.1:8000",
    ML_REQUEST_TIMEOUT_MS: 1000,
    NODE_ENV: "test",
  },
}));

jest.mock("../db/pool.js", () => ({
  pool: {
    query: jest.fn<any>(),
  },
}));

describe("ML price prediction backend integration", () => {
  const fetchMock = jest.fn<any>();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  test("calls FastAPI price prediction with service token and records result", async () => {
    const mlResult = {
      product_id: 10,
      predicted_price: 199.99,
      currency: "EUR",
      model_name: "product_price_prediction",
      model_version: "1.0",
      model_algorithm: "random_forest_regressor",
      metrics: { rmse: 12.5 },
      features_used: ["brand", "stock"],
    };

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: jest.fn<any>().mockResolvedValue(mlResult),
    });

    const result = await mlService.predictProductPrice({
      product_id: 10,
      brand: "Acme",
      stock: 15,
      tags: ["phone"],
    });

    expect(result).toEqual(mlResult);
    expect(String(fetchMock.mock.calls[0][0])).toBe("http://127.0.0.1:8000/price/predict");
    expect(fetchMock.mock.calls[0][1]).toEqual(expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({
        "Content-Type": "application/json",
        "X-ML-Service-Token": "a".repeat(32),
      }),
    }));
    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining("INSERT INTO product_price_predictions"),
      expect.arrayContaining([10, 199.99, "EUR", "product_price_prediction", "1.0"])
    );
  });

  test("surfaces ML service failures as backend gateway errors", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
      text: jest.fn<any>().mockResolvedValue("model missing"),
    });

    await expect(mlService.predictProductPrice({ title: "New product" }))
      .rejects.toThrow("ML price prediction failed");
  });
});

