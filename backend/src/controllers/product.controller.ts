import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { productService } from "../services/product.service.js";

export class ProductController {
  async getAllProducts(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await productService.getAllProducts(req.query);
      sendResponse(res, StatusCodes.OK, "Products retrieved", result);
    } catch (error) { next(error); }
  }

  async getProductById(req: Request, res: Response, next: NextFunction) {
    try {
      const product = await productService.getProductById(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "Product retrieved", product);
    } catch (error) { next(error); }
  }

  async createProduct(req: Request, res: Response, next: NextFunction) {
    try {
      // Handle uploaded images from multer
      if (req.files && Array.isArray(req.files)) {
        req.body.images = (req.files as Express.Multer.File[]).map(f => `/uploads/products/${f.filename}`);
        if (!req.body.thumbnail && req.body.images.length > 0) {
          req.body.thumbnail = req.body.images[0];
        }
      }
      const product = await productService.createProduct(req.body);
      sendResponse(res, StatusCodes.CREATED, "Product created", product);
    } catch (error) { next(error); }
  }

  async updateProduct(req: Request, res: Response, next: NextFunction) {
    try {
      if (req.files && Array.isArray(req.files) && req.files.length > 0) {
        req.body.images = (req.files as Express.Multer.File[]).map(f => `/uploads/products/${f.filename}`);
      }
      const product = await productService.updateProduct(Number(req.params.id), req.body);
      sendResponse(res, StatusCodes.OK, "Product updated", product);
    } catch (error) { next(error); }
  }

  async deleteProduct(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await productService.deleteProduct(Number(req.params.id));
      const msg = result.soft_deleted ? "Product deactivated (linked to orders)" : "Product deleted";
      sendResponse(res, StatusCodes.OK, msg);
    } catch (error) { next(error); }
  }
}

export const productController = new ProductController();
