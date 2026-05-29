import { jest } from "@jest/globals";
import { subcategoryController } from "../controllers/subcategory.controller.js";
import { subcategoryService } from "../services/subcategory.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/subcategory.service.js", () => ({
  subcategoryService: {
    getAll: jest.fn<any>(),
    getById: jest.fn<any>(),
    getByCategoryId: jest.fn<any>(),
    create: jest.fn<any>(),
    update: jest.fn<any>(),
    delete: jest.fn<any>(),
  },
}));

describe("SubcategoryController", () => {
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

  test("getAllSubcategories retrieves all subcategories", async () => {
    const list = [{ id: 1, name: "Phones", category_id: 1 }];
    (subcategoryService.getAll as any).mockResolvedValue(list);

    await subcategoryController.getAllSubcategories(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.getAll).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: list })
    );
  });

  test("getSubcategoryById returns by id", async () => {
    mockRequest.params = { id: "1" };
    const item = { id: 1, name: "Phones" };
    (subcategoryService.getById as any).mockResolvedValue(item);

    await subcategoryController.getSubcategoryById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.getById).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getByCategoryId filters by category", async () => {
    mockRequest.params = { categoryId: "5" };
    const items = [{ id: 1, category_id: 5 }];
    (subcategoryService.getByCategoryId as any).mockResolvedValue(items);

    await subcategoryController.getByCategoryId(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.getByCategoryId).toHaveBeenCalledWith(5);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("createSubcategory calls service create", async () => {
    mockRequest.body = { name: "Laptops", category_id: 1 };
    const created = { id: 3 };
    (subcategoryService.create as any).mockResolvedValue(created);

    await subcategoryController.createSubcategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.create).toHaveBeenCalledWith(mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(201);
  });

  test("updateSubcategory calls service update", async () => {
    mockRequest.params = { id: "1" };
    mockRequest.body = { name: "Modified Laptops" };
    (subcategoryService.update as any).mockResolvedValue({ id: 1 });

    await subcategoryController.updateSubcategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.update).toHaveBeenCalledWith(1, mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteSubcategory calls service delete", async () => {
    mockRequest.params = { id: "1" };
    (subcategoryService.delete as any).mockResolvedValue(undefined);

    await subcategoryController.deleteSubcategory(mockRequest as Request, mockResponse as Response, mockNext);

    expect(subcategoryService.delete).toHaveBeenCalledWith(1);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("DB error");
    (subcategoryService.getAll as any).mockRejectedValue(error);

    await subcategoryController.getAllSubcategories(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mockNext).toHaveBeenCalledWith(error);
  });
});
