import { jest } from "@jest/globals";
import { subcategoryController } from "../controllers/subcategory.controller.js";
import { subcategoryService } from "../services/subcategory.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/subcategory.service.js", () => {
  return {
    subcategoryService: {
      getAll: jest.fn<any>(),
      getById: jest.fn<any>(),
      getByCategoryId: jest.fn<any>(),
      create: jest.fn<any>(),
      update: jest.fn<any>(),
      delete: jest.fn<any>(),
    },
  };
});

describe("SubcategoryController Tests", () => {
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

  test("getAllSubcategories should retrieve all subcategories", async () => {
    const list = [{ id: 1, name: "Phones" }];
    (subcategoryService.getAll as any).mockResolvedValue(list);

    await subcategoryController.getAllSubcategories(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.getAll).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getSubcategoryById should return details", async () => {
    mockRequest.params = { id: "1" };
    (subcategoryService.getById as any).mockResolvedValue({ id: 1, name: "Phones" });

    await subcategoryController.getSubcategoryById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.getById).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getByCategoryId should filter subcategories", async () => {
    mockRequest.params = { categoryId: "5" };
    (subcategoryService.getByCategoryId as any).mockResolvedValue([{ id: 1, category_id: 5 }]);

    await subcategoryController.getByCategoryId(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.getByCategoryId).toHaveBeenCalledWith(5);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("createSubcategory should call create", async () => {
    mockRequest.body = { name: "Laptops", category_id: 1 };
    (subcategoryService.create as any).mockResolvedValue({ id: 3 });

    await subcategoryController.createSubcategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.create).toHaveBeenCalledWith(mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(201);
  });

  test("updateSubcategory should call update", async () => {
    mockRequest.params = { id: "1" };
    mockRequest.body = { name: "Modified Laptops" };
    (subcategoryService.update as any).mockResolvedValue({ id: 1 });

    await subcategoryController.updateSubcategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.update).toHaveBeenCalledWith(1, mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteSubcategory should call delete", async () => {
    mockRequest.params = { id: "1" };
    (subcategoryService.delete as any).mockResolvedValue(undefined);

    await subcategoryController.deleteSubcategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.delete).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });
});
