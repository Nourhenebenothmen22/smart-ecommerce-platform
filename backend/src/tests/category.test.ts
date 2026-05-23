import { jest } from "@jest/globals";
import { categoryController } from "../controllers/category.controller.js";
import { categoryService } from "../services/category.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/category.service.js", () => {
  return {
    categoryService: {
      getAll: jest.fn<any>(),
      getById: jest.fn<any>(),
      create: jest.fn<any>(),
      update: jest.fn<any>(),
      delete: jest.fn<any>(),
    },
  };
});

describe("CategoryController Tests", () => {
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
      body: {},
    };
    mockResponse = {
      status: statusMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getAllCategories should retrieve all categories", async () => {
    const list = [{ id: 1, name: "Electronics" }];
    (categoryService.getAll as any).mockResolvedValue(list);

    await categoryController.getAllCategories(mockRequest as Request, mockResponse as Response, mockNext);

    expect(categoryService.getAll).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        data: list,
      })
    );
  });

  test("getCategoryById should return category details", async () => {
    mockRequest.params = { id: "1" };
    const cat = { id: 1, name: "Electronics" };
    (categoryService.getById as any).mockResolvedValue(cat);

    await categoryController.getCategoryById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(categoryService.getById).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("createCategory should call create", async () => {
    mockRequest.body = { name: "Fashion" };
    const created = { id: 2, name: "Fashion" };
    (categoryService.create as any).mockResolvedValue(created);

    await categoryController.createCategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(categoryService.create).toHaveBeenCalledWith(mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(201);
  });

  test("updateCategory should call update", async () => {
    mockRequest.params = { id: "1" };
    mockRequest.body = { name: "New Name" };
    (categoryService.update as any).mockResolvedValue({ id: 1, name: "New Name" });

    await categoryController.updateCategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(categoryService.update).toHaveBeenCalledWith(1, mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteCategory should call delete", async () => {
    mockRequest.params = { id: "1" };
    (categoryService.delete as any).mockResolvedValue(undefined);

    await categoryController.deleteCategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(categoryService.delete).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });
});
