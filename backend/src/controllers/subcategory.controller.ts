import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { subcategoryService } from "../services/subcategory.service.js";

export class SubcategoryController {
  async getAllSubcategories(_req: Request, res: Response, next: NextFunction) {
    try {
      const data = await subcategoryService.getAll();
      sendResponse(res, StatusCodes.OK, "Subcategories retrieved", data);
    } catch (error) { next(error); }
  }

  async getSubcategoryById(req: Request, res: Response, next: NextFunction) {
    try {
      const data = await subcategoryService.getById(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "Subcategory retrieved", data);
    } catch (error) { next(error); }
  }

  async getByCategoryId(req: Request, res: Response, next: NextFunction) {
    try {
      const data = await subcategoryService.getByCategoryId(Number(req.params.categoryId));
      sendResponse(res, StatusCodes.OK, "Subcategories retrieved", data);
    } catch (error) { next(error); }
  }

  async createSubcategory(req: Request, res: Response, next: NextFunction) {
    try {
      const data = await subcategoryService.create(req.body);
      sendResponse(res, StatusCodes.CREATED, "Subcategory created", data);
    } catch (error) { next(error); }
  }

  async updateSubcategory(req: Request, res: Response, next: NextFunction) {
    try {
      const data = await subcategoryService.update(Number(req.params.id), req.body);
      sendResponse(res, StatusCodes.OK, "Subcategory updated", data);
    } catch (error) { next(error); }
  }

  async deleteSubcategory(req: Request, res: Response, next: NextFunction) {
    try {
      await subcategoryService.delete(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "Subcategory deleted");
    } catch (error) { next(error); }
  }
}

export const subcategoryController = new SubcategoryController();
