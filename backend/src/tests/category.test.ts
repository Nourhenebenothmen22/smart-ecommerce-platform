import { jest } from "@jest/globals";
import { categoryController } from "../controllers/category.controller.js";
import { categoryService } from "../services/category.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

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
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: null });
    jest.clearAllMocks();
  });

  test("getAllCategories retrieves all categories", async () => {
    const list = [{ id: 1, name: "Electronics" }];
    (categoryService.getAll as any).mockResolvedValue(list);

    await categoryController.getAllCategories(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(categoryService.getAll).toHaveBeenCalled();
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: list })
    );
  });

  test("getCategoryById returns category by id", async () => {
    ctx.mockRequest.params = { id: "1" };
    const cat = { id: 1, name: "Electronics" };
    (categoryService.getById as any).mockResolvedValue(cat);

    await categoryController.getCategoryById(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(categoryService.getById).toHaveBeenCalledWith(1);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards error to next handler on service failure", async () => {
    const error = new Error("DB error");
    (categoryService.getAll as any).mockRejectedValue(error);

    await categoryController.getAllCategories(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
