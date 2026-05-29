import { jest } from "@jest/globals";
import { reviewController } from "../controllers/review.controller.js";
import { reviewService } from "../services/review.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/review.service.js", () => ({
  reviewService: {
    getByProductId: jest.fn<any>(),
    create: jest.fn<any>(),
    update: jest.fn<any>(),
    delete: jest.fn<any>(),
  },
}));

describe("ReviewController", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = { params: {}, query: {}, body: {}, user: { id: 22, role: "customer", email: "user@example.com" } };
    mockResponse = { status: statusMock };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getProductReviews retrieves paginated reviews for a product", async () => {
    mockRequest.params = { productId: "5" };
    mockRequest.query = { page: "1", limit: "10" };
    const result = { reviews: [], total: 0 };
    (reviewService.getByProductId as any).mockResolvedValue(result);

    await reviewController.getProductReviews(mockRequest as Request, mockResponse as Response, mockNext);

    expect(reviewService.getByProductId).toHaveBeenCalledWith(5, 1, 10);
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: result })
    );
  });

  test("getProductReviews uses legacy route param (id) when productId missing", async () => {
    mockRequest.params = { id: "5" };
    mockRequest.query = { page: "1", limit: "20" };
    const result = { reviews: [], total: 0 };
    (reviewService.getByProductId as any).mockResolvedValue(result);

    await reviewController.getProductReviews(mockRequest as Request, mockResponse as Response, mockNext);

    expect(reviewService.getByProductId).toHaveBeenCalledWith(5, 1, 20);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("Review service error");
    (reviewService.getByProductId as any).mockRejectedValue(error);

    mockRequest.params = { productId: "5" };
    await reviewController.getProductReviews(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mockNext).toHaveBeenCalledWith(error);
  });
});
