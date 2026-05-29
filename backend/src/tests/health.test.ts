import { jest } from "@jest/globals";
import { healthController } from "../controllers/health.controller.js";
import { Request, Response } from "express";

describe("HealthController", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = {};
    mockResponse = { status: statusMock, json: jsonMock };
    jest.clearAllMocks();
  });

  test("check returns 200 with healthy status", async () => {
    await healthController.check(mockRequest as Request, mockResponse as Response);

    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        status: "success",
        message: "Server is healthy",
        timestamp: expect.any(String),
      })
    );
  });
});
