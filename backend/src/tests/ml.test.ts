import { jest } from "@jest/globals";
import { mlController } from "../controllers/ml.controller.js";
import { mlService } from "../services/ml.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/ml.service.js", () => ({
  mlService: {
    recalculateUserFeatures: jest.fn<any>(),
    recordUserSegments: jest.fn<any>(),
    registerModel: jest.fn<any>(),
    predictProductPrice: jest.fn<any>(),
  },
}));

describe("MLController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: null });
    jest.clearAllMocks();
  });

  describe("recalculateFeatures", () => {
    test("triggers features recalculation", async () => {
      (mlService.recalculateUserFeatures as any).mockResolvedValue(undefined);

      await mlController.recalculateFeatures(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.recalculateUserFeatures).toHaveBeenCalled();
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
      expect(ctx.jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({ success: true })
      );
    });

    test("forwards errors to next handler", async () => {
      const error = new Error("ML service unavailable");
      (mlService.recalculateUserFeatures as any).mockRejectedValue(error);

      await mlController.recalculateFeatures(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(ctx.mockNext).toHaveBeenCalledWith(error);
    });
  });

  describe("updateSegments", () => {
    test("validates body and calls recordUserSegments", async () => {
      ctx.mockRequest.body = {
        segments: [{
          user_id: 1,
          segment_id: 2,
          segment_label: "High Value",
          model_name: "kmeans",
          model_version: "v1.0",
        }],
      };
      (mlService.recordUserSegments as any).mockResolvedValue(undefined);

      await mlController.updateSegments(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.recordUserSegments).toHaveBeenCalledWith(ctx.mockRequest.body.segments);
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });

    test("returns 400 if validation fails (empty segments)", async () => {
      ctx.mockRequest.body = { segments: [] };

      await mlController.updateSegments(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.recordUserSegments).not.toHaveBeenCalled();
      expect(ctx.statusMock).toHaveBeenCalledWith(400);
    });

    test("returns 400 if segments field missing", async () => {
      ctx.mockRequest.body = {};

      await mlController.updateSegments(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.recordUserSegments).not.toHaveBeenCalled();
      expect(ctx.statusMock).toHaveBeenCalledWith(400);
    });
  });

  describe("registerModel", () => {
    test("validates details and calls registerModel", async () => {
      ctx.mockRequest.body = {
        model_name: "kmeans_customer",
        model_version: "1.0.0",
        model_type: "segmentation",
        algorithm: "kmeans",
      };
      (mlService.registerModel as any).mockResolvedValue(undefined);

      await mlController.registerModel(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.registerModel).toHaveBeenCalledWith(ctx.mockRequest.body);
      expect(ctx.statusMock).toHaveBeenCalledWith(201);
    });

    test("returns 400 if model_name missing", async () => {
      ctx.mockRequest.body = { model_version: "1.0.0", model_type: "segmentation", algorithm: "kmeans" };

      await mlController.registerModel(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.registerModel).not.toHaveBeenCalled();
      expect(ctx.statusMock).toHaveBeenCalledWith(400);
    });
  });

  describe("predictProductPrice", () => {
    test("validates body and calls predictProductPrice", async () => {
      ctx.mockRequest.body = { product_id: 10, brand: "Acme", stock: 15 };
      const result = { predicted_price: 199.99 };
      (mlService.predictProductPrice as any).mockResolvedValue(result);

      await mlController.predictProductPrice(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.predictProductPrice).toHaveBeenCalledWith({
        product_id: 10, brand: "Acme", stock: 15,
      });
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });

    test("returns 400 for empty body", async () => {
      ctx.mockRequest.body = {};

      await mlController.predictProductPrice(
        ctx.mockRequest as Request,
        ctx.mockResponse as Response,
        ctx.mockNext
      );

      expect(mlService.predictProductPrice).not.toHaveBeenCalled();
      expect(ctx.statusMock).toHaveBeenCalledWith(400);
    });
  });
});
