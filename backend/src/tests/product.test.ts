import { jest } from "@jest/globals";
import { productController } from "../controllers/product.controller.js";
import { productService } from "../services/product.service.js";
import { Request, Response, NextFunction } from "express";

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
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = { params: {}, query: {}, body: {} };
    mockResponse = { status: statusMock };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getAllProducts retrieves paginated products", async () => {
    mockRequest.query = { limit: "10", page: "1" };
    const result = { products: [], total: 0 };
    (productService.getAllProducts as any).mockResolvedValue(result);

    await productController.getAllProducts(mockRequest as Request, mockResponse as Response, mockNext);

    expect(productService.getAllProducts).toHaveBeenCalledWith(mockRequest.query);
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: result })
    );
  });

  test("getProductById returns product details", async () => {
    mockRequest.params = { id: "1" };
    const product = { id: 1, title: "Phone" };
    (productService.getProductById as any).mockResolvedValue(product);

    await productController.getProductById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(productService.getProductById).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("Product not found");
    (productService.getProductById as any).mockRejectedValue(error);

    mockRequest.params = { id: "999" };
    await productController.getProductById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mockNext).toHaveBeenCalledWith(error);
  });
});
