import { jest } from "@jest/globals";
import { categoryController } from "../controllers/category.controller.js";
import { categoryService } from "../services/category.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/category.service.js", () => ({
  categoryService: {
    getAll: jest.fn<any>(),
    getById: jest.fn<any>(),
    create: jest.fn<any>(),
    update: jest.fn<any>(),
    delete: jest.fn<any>(),
  },
}));

describe("CategoryController", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = { params: {}, body: {}, query: {} };
    mockResponse = { status: statusMock };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getAllCategories retrieves all categories", async () => {
    const list = [{ id: 1, name: "Electronics" }];
    (categoryService.getAll as any).mockResolvedValue(list);

    await categoryController.getAllCategories(mockRequest as Request, mockResponse as Response, mockNext);

    expect(categoryService.getAll).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: list })
    );
  });

  test("getCategoryById returns category by id", async () => {
    mockRequest.params = { id: "1" };
    const cat = { id: 1, name: "Electronics" };
    (categoryService.getById as any).mockResolvedValue(cat);

    await categoryController.getCategoryById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(categoryService.getById).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards error to next handler on service failure", async () => {
    const error = new Error("DB error");
    (categoryService.getAll as any).mockRejectedValue(error);

    await categoryController.getAllCategories(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mockNext).toHaveBeenCalledWith(error);
  });
});
