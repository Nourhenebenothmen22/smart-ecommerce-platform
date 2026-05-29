import { jest } from "@jest/globals";
import { mlController } from "../controllers/ml.controller.js";
import { mlService } from "../services/ml.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/ml.service.js", () => ({
  mlService: {
    recalculateUserFeatures: jest.fn<any>(),
    recordUserSegments: jest.fn<any>(),
    registerModel: jest.fn<any>(),
    predictProductPrice: jest.fn<any>(),
  },
}));

describe("MLController", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = { params: {}, body: {}, query: {} };
    mockResponse = { status: statusMock };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  describe("recalculateFeatures", () => {
    test("triggers features recalculation", async () => {
      (mlService.recalculateUserFeatures as any).mockResolvedValue(undefined);

      await mlController.recalculateFeatures(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.recalculateUserFeatures).toHaveBeenCalled();
      expect(statusMock).toHaveBeenCalledWith(200);
      expect(jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({ success: true })
      );
    });

    test("forwards errors to next handler", async () => {
      const error = new Error("ML service unavailable");
      (mlService.recalculateUserFeatures as any).mockRejectedValue(error);

      await mlController.recalculateFeatures(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mockNext).toHaveBeenCalledWith(error);
    });
  });

  describe("updateSegments", () => {
    test("validates body and calls recordUserSegments", async () => {
      mockRequest.body = {
        segments: [{
          user_id: 1,
          segment_id: 2,
          segment_label: "High Value",
          model_name: "kmeans",
          model_version: "v1.0",
        }],
      };
      (mlService.recordUserSegments as any).mockResolvedValue(undefined);

      await mlController.updateSegments(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.recordUserSegments).toHaveBeenCalledWith(mockRequest.body.segments);
      expect(statusMock).toHaveBeenCalledWith(200);
    });

    test("returns 400 if validation fails (empty segments)", async () => {
      mockRequest.body = { segments: [] };

      await mlController.updateSegments(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.recordUserSegments).not.toHaveBeenCalled();
      expect(statusMock).toHaveBeenCalledWith(400);
    });

    test("returns 400 if segments field missing", async () => {
      mockRequest.body = {};

      await mlController.updateSegments(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.recordUserSegments).not.toHaveBeenCalled();
      expect(statusMock).toHaveBeenCalledWith(400);
    });
  });

  describe("registerModel", () => {
    test("validates details and calls registerModel", async () => {
      mockRequest.body = {
        model_name: "kmeans_customer",
        model_version: "1.0.0",
        model_type: "segmentation",
        algorithm: "kmeans",
      };
      (mlService.registerModel as any).mockResolvedValue(undefined);

      await mlController.registerModel(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.registerModel).toHaveBeenCalledWith(mockRequest.body);
      expect(statusMock).toHaveBeenCalledWith(201);
    });

    test("returns 400 if model_name missing", async () => {
      mockRequest.body = { model_version: "1.0.0", model_type: "segmentation", algorithm: "kmeans" };

      await mlController.registerModel(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.registerModel).not.toHaveBeenCalled();
      expect(statusMock).toHaveBeenCalledWith(400);
    });
  });

  describe("predictProductPrice", () => {
    test("validates body and calls predictProductPrice", async () => {
      mockRequest.body = { product_id: 10, brand: "Acme", stock: 15 };
      const result = { predicted_price: 199.99 };
      (mlService.predictProductPrice as any).mockResolvedValue(result);

      await mlController.predictProductPrice(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.predictProductPrice).toHaveBeenCalledWith({
        product_id: 10, brand: "Acme", stock: 15,
      });
      expect(statusMock).toHaveBeenCalledWith(200);
    });

    test("returns 400 for empty body", async () => {
      mockRequest.body = {};

      await mlController.predictProductPrice(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mlService.predictProductPrice).not.toHaveBeenCalled();
      expect(statusMock).toHaveBeenCalledWith(400);
    });
  });
});
