import { jest } from "@jest/globals";
import { reviewController } from "../controllers/review.controller.js";
import { reviewService } from "../services/review.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/review.service.js", () => ({
  reviewService: {
    getByProductId: jest.fn<any>(),
    create: jest.fn<any>(),
    update: jest.fn<any>(),
    delete: jest.fn<any>(),
  },
}));

describe("ReviewController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: { id: 22, role: "customer", email: "user@example.com" } });
    jest.clearAllMocks();
  });

  test("getProductReviews retrieves paginated reviews for a product", async () => {
    ctx.mockRequest.params = { productId: "5" };
    ctx.mockRequest.query = { page: "1", limit: "10" };
    const result = { reviews: [], total: 0 };
    (reviewService.getByProductId as any).mockResolvedValue(result);

    await reviewController.getProductReviews(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(reviewService.getByProductId).toHaveBeenCalledWith(5, 1, 10);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: result })
    );
  });

  test("getProductReviews uses legacy route param (id) when productId missing", async () => {
    ctx.mockRequest.params = { id: "5" };
    ctx.mockRequest.query = { page: "1", limit: "20" };
    const result = { reviews: [], total: 0 };
    (reviewService.getByProductId as any).mockResolvedValue(result);

    await reviewController.getProductReviews(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(reviewService.getByProductId).toHaveBeenCalledWith(5, 1, 20);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("Review service error");
    (reviewService.getByProductId as any).mockRejectedValue(error);
    ctx.mockRequest.params = { productId: "5" };

    await reviewController.getProductReviews(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
