import { jest } from "@jest/globals";
import { productController } from "../controllers/product.controller.js";
import { productService } from "../services/product.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/product.service.js", () => {
  return {
    productService: {
      getAllProducts: jest.fn<any>(),
      getProductById: jest.fn<any>(),
      createProduct: jest.fn<any>(),
      updateProduct: jest.fn<any>(),
      deleteProduct: jest.fn<any>(),
    },
  };
});

describe("ProductController Tests", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = {
      params: {},
      query: {},
      body: {},
    };
    mockResponse = {
      status: statusMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getAllProducts should retrieve products list", async () => {
    mockRequest.query = { limit: "10" };
    (productService.getAllProducts as any).mockResolvedValue({ products: [], total: 0 });

    await productController.getAllProducts(mockRequest as Request, mockResponse as Response, mockNext);

    expect(productService.getAllProducts).toHaveBeenCalledWith(mockRequest.query);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getProductById should return product details", async () => {
    mockRequest.params = { id: "1" };
    (productService.getProductById as any).mockResolvedValue({ id: 1, title: "Phone" });

    await productController.getProductById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(productService.getProductById).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("createProduct should create a new product", async () => {
    mockRequest.body = { title: "New Phone", price: 500 };
    (productService.createProduct as any).mockResolvedValue({ id: 10, title: "New Phone" });

    await productController.createProduct(mockRequest as Request, mockResponse as Response, mockNext);

    expect(productService.createProduct).toHaveBeenCalledWith(mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(201);
  });

  test("updateProduct should update a product", async () => {
    mockRequest.params = { id: "1" };
    mockRequest.body = { price: 450 };
    (productService.updateProduct as any).mockResolvedValue({ id: 1, price: 450 });

    await productController.updateProduct(mockRequest as Request, mockResponse as Response, mockNext);

    expect(productService.updateProduct).toHaveBeenCalledWith(1, mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteProduct should delete a product", async () => {
    mockRequest.params = { id: "1" };
    (productService.deleteProduct as any).mockResolvedValue({ soft_deleted: false });

    await productController.deleteProduct(mockRequest as Request, mockResponse as Response, mockNext);

    expect(productService.deleteProduct).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });
});
