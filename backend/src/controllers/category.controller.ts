import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { categoryService } from "../services/category.service.js";

export class CategoryController {
  async getAllCategories(_req: Request, res: Response, next: NextFunction) {
    try {
      const categories = await categoryService.getAll();
      sendResponse(res, StatusCodes.OK, "Categories retrieved", categories);
    } catch (error) { next(error); }
  }

  async getCategoryById(req: Request, res: Response, next: NextFunction) {
    try {
      const category = await categoryService.getById(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "Category retrieved", category);
    } catch (error) { next(error); }
  }

  async createCategory(req: Request, res: Response, next: NextFunction) {
    try {
      const category = await categoryService.create(req.body);
      sendResponse(res, StatusCodes.CREATED, "Category created", category);
    } catch (error) { next(error); }
  }

  async updateCategory(req: Request, res: Response, next: NextFunction) {
    try {
      const category = await categoryService.update(Number(req.params.id), req.body);
      sendResponse(res, StatusCodes.OK, "Category updated", category);
    } catch (error) { next(error); }
  }

  async deleteCategory(req: Request, res: Response, next: NextFunction) {
    try {
      await categoryService.delete(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "Category deleted");
    } catch (error) { next(error); }
  }
}

export const categoryController = new CategoryController();
