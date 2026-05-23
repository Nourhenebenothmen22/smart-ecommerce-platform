import { jest } from "@jest/globals";
import { reviewController } from "../controllers/review.controller.js";
import { reviewService } from "../services/review.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/review.service.js", () => {
  return {
    reviewService: {
      getByProductId: jest.fn<any>(),
      create: jest.fn<any>(),
      update: jest.fn<any>(),
      delete: jest.fn<any>(),
    },
  };
});

describe("ReviewController Tests", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = {
      params: {},
      query: {},
      body: {},
      user: { id: 22, email: "user@example.com", role: "customer" },
    };
    mockResponse = {
      status: statusMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getProductReviews should retrieve reviews list", async () => {
    mockRequest.params = { productId: "5" };
    mockRequest.query = { page: "1", limit: "10" };
    (reviewService.getByProductId as any).mockResolvedValue({ reviews: [], total: 0 });

    await reviewController.getProductReviews(mockRequest as Request, mockResponse as Response, mockNext);

    expect(reviewService.getByProductId).toHaveBeenCalledWith(5, 1, 10);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("addReview should add a new review", async () => {
    mockRequest.body = { product_id: 5, rating: 5, review_text: "Perfect!" };
    (reviewService.create as any).mockResolvedValue({ id: 1 });

    await reviewController.addReview(mockRequest as Request, mockResponse as Response, mockNext);

    expect(reviewService.create).toHaveBeenCalledWith(22, {
      product_id: 5,
      rating: 5,
      review_text: "Perfect!",
    });
    expect(statusMock).toHaveBeenCalledWith(201);
  });

  test("updateReview should update a review", async () => {
    mockRequest.params = { id: "1" };
    mockRequest.body = { rating: 4 };
    (reviewService.update as any).mockResolvedValue({ id: 1, rating: 4 });

    await reviewController.updateReview(mockRequest as Request, mockResponse as Response, mockNext);

    expect(reviewService.update).toHaveBeenCalledWith(1, 22, "customer", mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteReview should call delete", async () => {
    mockRequest.params = { id: "1" };
    (reviewService.delete as any).mockResolvedValue(undefined);

    await reviewController.deleteReview(mockRequest as Request, mockResponse as Response, mockNext);

    expect(reviewService.delete).toHaveBeenCalledWith(1, 22, "customer");
    expect(statusMock).toHaveBeenCalledWith(200);
  });
});
