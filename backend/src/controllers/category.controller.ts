import { Request, Response, NextFunction } from 'express';
import { StatusCodes } from 'http-status-codes';
import { sendResponse } from '../utils/apiResponse.js';

export class CategoryController {
  async getAllCategories(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetAllCategories not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async getCategoryById(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetCategoryById not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async createCategory(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'CreateCategory not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async updateCategory(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }

  async deleteCategory(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }
}

export const categoryController = new CategoryController();
