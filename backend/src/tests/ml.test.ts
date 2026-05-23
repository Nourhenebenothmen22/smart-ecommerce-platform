import { jest } from "@jest/globals";
import { mlController } from "../controllers/ml.controller.js";
import { mlService } from "../services/ml.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/ml.service.js", () => {
  return {
    mlService: {
      recalculateUserFeatures: jest.fn<any>(),
      recordUserSegments: jest.fn<any>(),
      registerModel: jest.fn<any>(),
    },
  };
});

describe("MLController Tests", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = {
      body: {},
    };
    mockResponse = {
      status: statusMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("recalculateFeatures should trigger user features recalculation", async () => {
    (mlService.recalculateUserFeatures as any).mockResolvedValue(undefined);

    await mlController.recalculateFeatures(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mlService.recalculateUserFeatures).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("updateSegments should validate body and call recordUserSegments", async () => {
    mockRequest.body = {
      segments: [
        {
          user_id: 1,
          segment_id: 2,
          segment_label: "High Value",
          model_name: "kmeans",
          model_version: "v1.0",
        },
      ],
    };
    (mlService.recordUserSegments as any).mockResolvedValue(undefined);

    await mlController.updateSegments(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mlService.recordUserSegments).toHaveBeenCalledWith(mockRequest.body.segments);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("updateSegments should return 400 if validation fails", async () => {
    mockRequest.body = { segments: [] }; // Empty segments array

    await mlController.updateSegments(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mlService.recordUserSegments).not.toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(400);
  });

  test("registerModel should validate details and call registerModel", async () => {
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
});
