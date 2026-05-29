import { jest } from "@jest/globals";
import { subcategoryController } from "../controllers/subcategory.controller.js";
import { subcategoryService } from "../services/subcategory.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

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
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: null });
    jest.clearAllMocks();
  });

  test("getAllSubcategories retrieves all subcategories", async () => {
    const list = [{ id: 1, name: "Phones", category_id: 1 }];
    (subcategoryService.getAll as any).mockResolvedValue(list);

    await subcategoryController.getAllSubcategories(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(subcategoryService.getAll).toHaveBeenCalled();
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: list })
    );
  });

  test("getSubcategoryById returns by id", async () => {
    ctx.mockRequest.params = { id: "1" };
    const item = { id: 1, name: "Phones" };
    (subcategoryService.getById as any).mockResolvedValue(item);

    await subcategoryController.getSubcategoryById(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(subcategoryService.getById).toHaveBeenCalledWith(1);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("getByCategoryId filters by category", async () => {
    ctx.mockRequest.params = { categoryId: "5" };
    const items = [{ id: 1, category_id: 5 }];
    (subcategoryService.getByCategoryId as any).mockResolvedValue(items);

    await subcategoryController.getByCategoryId(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(subcategoryService.getByCategoryId).toHaveBeenCalledWith(5);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("createSubcategory calls service create", async () => {
    ctx.mockRequest.body = { name: "Laptops", category_id: 1 };
    const created = { id: 3 };
    (subcategoryService.create as any).mockResolvedValue(created);

    await subcategoryController.createSubcategory(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(subcategoryService.create).toHaveBeenCalledWith(ctx.mockRequest.body);
    expect(ctx.statusMock).toHaveBeenCalledWith(201);
  });

  test("updateSubcategory calls service update", async () => {
    ctx.mockRequest.params = { id: "1" };
    ctx.mockRequest.body = { name: "Modified Laptops" };
    (subcategoryService.update as any).mockResolvedValue({ id: 1 });

    await subcategoryController.updateSubcategory(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(subcategoryService.update).toHaveBeenCalledWith(1, ctx.mockRequest.body);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteSubcategory calls service delete", async () => {
    ctx.mockRequest.params = { id: "1" };
    (subcategoryService.delete as any).mockResolvedValue(undefined);

    await subcategoryController.deleteSubcategory(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(subcategoryService.delete).toHaveBeenCalledWith(1);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("DB error");
    (subcategoryService.getAll as any).mockRejectedValue(error);

    await subcategoryController.getAllSubcategories(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
