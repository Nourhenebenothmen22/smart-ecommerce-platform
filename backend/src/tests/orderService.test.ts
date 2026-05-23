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

  test("rejects invalid terminal status transitions", async () => {
    const client = {
      query: jest.fn<any>()
        .mockResolvedValueOnce({ rows: [{ id: 123, status: "cancelled" }] }),
    };

    await expect(orderService.updateStatus(123, "processing", client as any))
      .rejects.toThrow('Invalid order status transition from "cancelled" to "processing"');
  });

  test("restores stock when cancelling an active order", async () => {
    const client = {
      query: jest.fn<any>()
        .mockResolvedValueOnce({ rows: [{ id: 123, status: "processing" }] })
        .mockResolvedValueOnce({ rows: [{ product_id: 10, quantity: 2 }] })
        .mockResolvedValueOnce({ rows: [] })
        .mockResolvedValueOnce({ rows: [{ id: 123, status: "cancelled" }] }),
    };

    const result = await orderService.updateStatus(123, "cancelled", client as any);

    expect(client.query).toHaveBeenCalledWith(
      "UPDATE products SET stock=stock+$1,updated_at=NOW() WHERE id=$2",
      [2, 10]
    );
    expect(result).toEqual({ id: 123, status: "cancelled" });
  });

  test("deleteOrder performs a safe cancellation instead of hard delete", async () => {
    const client = {
      query: jest.fn<any>()
        .mockResolvedValueOnce({ rows: [] })
        .mockResolvedValueOnce({ rows: [{ id: 123, status: "processing" }] })
        .mockResolvedValueOnce({ rows: [] })
        .mockResolvedValueOnce({ rows: [{ id: 123, status: "cancelled" }] })
        .mockResolvedValueOnce({ rows: [] }),
      release: jest.fn(),
    };
    (pool.connect as any).mockResolvedValue(client);

    await orderService.deleteOrder(123);

    expect(client.query).not.toHaveBeenCalledWith("DELETE FROM orders WHERE id=$1 RETURNING id", [123]);
    expect(client.query).toHaveBeenCalledWith(
      "UPDATE orders SET status=$1, updated_at=NOW() WHERE id=$2 RETURNING *",
      ["cancelled", 123]
    );
  });
});
