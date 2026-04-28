import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { reviewService } from "../services/review.service.js";

export class ReviewController {
  async getProductReviews(req: Request, res: Response, next: NextFunction) {
    try {
      const productId = Number(req.params.productId || req.params.id);
      const page = Number(req.query.page) || 1;
      const limit = Number(req.query.limit) || 20;
      const result = await reviewService.getByProductId(productId, page, limit);
      sendResponse(res, StatusCodes.OK, "Reviews retrieved", result);
    } catch (error) { next(error); }
  }

  async addReview(req: Request, res: Response, next: NextFunction) {
    try {
      const review = await reviewService.create(req.user!.id, {
        product_id: req.body.product_id,
        rating: req.body.rating,
        review_text: req.body.review_text,
      });
      sendResponse(res, StatusCodes.CREATED, "Review created", review);
    } catch (error) { next(error); }
  }

  async updateReview(req: Request, res: Response, next: NextFunction) {
    try {
      const review = await reviewService.update(
        Number(req.params.id), req.user!.id, req.user!.role, req.body
      );
      sendResponse(res, StatusCodes.OK, "Review updated", review);
    } catch (error) { next(error); }
  }

  async deleteReview(req: Request, res: Response, next: NextFunction) {
    try {
      await reviewService.delete(Number(req.params.id), req.user!.id, req.user!.role);
      sendResponse(res, StatusCodes.OK, "Review deleted");
    } catch (error) { next(error); }
  }
}

export const reviewController = new ReviewController();
