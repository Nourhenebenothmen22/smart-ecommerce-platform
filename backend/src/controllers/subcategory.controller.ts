import { Request, Response, NextFunction } from 'express';
import { StatusCodes } from 'http-status-codes';
import { sendResponse } from '../utils/apiResponse.js';

export class SubcategoryController {
  async getAllSubcategories(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetAllSubcategories not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async getSubcategoryById(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetSubcategoryById not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async createSubcategory(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'CreateSubcategory not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async updateSubcategory(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }

  async deleteSubcategory(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }
}

export const subcategoryController = new SubcategoryController();
