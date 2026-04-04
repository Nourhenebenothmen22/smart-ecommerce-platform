import { Request, Response, NextFunction } from 'express';

export class SubcategoryController {
  async getAllSubcategories(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }

  async getSubcategoryById(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }

  async createSubcategory(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
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
