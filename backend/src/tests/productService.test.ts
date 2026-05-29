import { jest } from "@jest/globals";
import { productService } from "../services/product.service.js";
import { pool } from "../db/pool.js";

jest.mock("../db/pool.js", () => ({
  pool: { query: jest.fn<any>() },
}));

describe("ProductService validation", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("validates effective category/subcategory pair on partial update", async () => {
    (pool.query as any)
      .mockResolvedValueOnce({ rows: [{ id: 10, category_id: 1, subcategory_id: 2 }] })
      .mockResolvedValueOnce({ rows: [] });

    await expect(productService.updateProduct(10, { category_id: 3 }))
      .rejects.toThrow("Subcategory does not belong to category");

    expect(pool.query).toHaveBeenNthCalledWith(
      2,
      "SELECT id FROM subcategories WHERE id=$1 AND category_id=$2",
      [2, 3]
    );
  });

  test("returns not found before attempting update", async () => {
    (pool.query as any).mockResolvedValueOnce({ rows: [] });

    await expect(productService.updateProduct(10, { price: 99 }))
      .rejects.toThrow("Product not found");
  });
});
