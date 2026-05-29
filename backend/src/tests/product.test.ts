import { jest } from "@jest/globals";
import { productController } from "../controllers/product.controller.js";
import { productService } from "../services/product.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/product.service.js", () => ({
  productService: {
    getAllProducts: jest.fn<any>(),
    getProductById: jest.fn<any>(),
    createProduct: jest.fn<any>(),
    updateProduct: jest.fn<any>(),
    deleteProduct: jest.fn<any>(),
  },
}));

describe("ProductController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: null });
    jest.clearAllMocks();
  });

  test("getAllProducts retrieves paginated products", async () => {
    ctx.mockRequest.query = { limit: "10", page: "1" };
    const result = { products: [], total: 0 };
    (productService.getAllProducts as any).mockResolvedValue(result);

    await productController.getAllProducts(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(productService.getAllProducts).toHaveBeenCalledWith(ctx.mockRequest.query);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: result })
    );
  });

  test("getProductById returns product details", async () => {
    ctx.mockRequest.params = { id: "1" };
    const product = { id: 1, title: "Phone" };
    (productService.getProductById as any).mockResolvedValue(product);

    await productController.getProductById(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(productService.getProductById).toHaveBeenCalledWith(1);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("Product not found");
    (productService.getProductById as any).mockRejectedValue(error);
    ctx.mockRequest.params = { id: "999" };

    await productController.getProductById(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
