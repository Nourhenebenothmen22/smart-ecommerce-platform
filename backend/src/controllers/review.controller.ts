import { Request, Response, NextFunction } from 'express';
import { StatusCodes } from 'http-status-codes';
import { sendResponse } from '../utils/apiResponse.js';

export class ReviewController {
  async addReview(req: Request, res: Response, next: NextFunction) {
    try {
      // Logic for adding a product review
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "AddReview not implemented yet");
    } catch (error) {
      next(error);
    }
  }

  async getProductReviews(req: Request, res: Response, next: NextFunction) {
    try {
      // Logic for retrieving reviews for a specific product
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "GetProductReviews not implemented yet");
    } catch (error) {
      next(error);
    }
  }

  async deleteReview(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "DeleteReview not implemented yet");
    } catch (error) {
      next(error);
    }
  }
}

export const reviewController = new ReviewController();
