import { jest } from "@jest/globals";
import { orderService } from "../services/order.service.js";
import { pool } from "../db/pool.js";

jest.mock("../db/pool.js", () => {
  return {
    pool: {
      connect: jest.fn<any>(),
      query: jest.fn<any>(),
    },
  };
});

describe("OrderService transaction behavior", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("uses an existing transaction client when provided", async () => {
    const client = {
      query: jest.fn<any>()
        .mockResolvedValueOnce({ rows: [{ id: 123, status: "pending_phone_confirmation" }] })
        .mockResolvedValueOnce({ rows: [{ id: 123, status: "processing" }] }),
    };

    const result = await orderService.updateStatus(123, "processing", client as any);

    expect(pool.connect).not.toHaveBeenCalled();
    expect(client.query).not.toHaveBeenCalledWith("BEGIN");
    expect(client.query).not.toHaveBeenCalledWith("COMMIT");
    expect(result).toEqual({ id: 123, status: "processing" });
  });
});
