import { Request, Response, NextFunction } from 'express';
import { StatusCodes } from 'http-status-codes';
import { sendResponse } from '../utils/apiResponse.js';

export class ProductController {
  async getAllProducts(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetAllProducts not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async getProductById(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetProductById not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async createProduct(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'CreateProduct not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async updateProduct(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }

  async deleteProduct(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }
}

export const productController = new ProductController();
