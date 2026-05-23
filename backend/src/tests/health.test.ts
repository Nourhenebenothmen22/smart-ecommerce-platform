import { jest } from "@jest/globals";
import { healthController } from "../controllers/health.controller.js";
import { Request, Response } from "express";

describe("HealthController Tests", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Response;
  let jsonMock: jest.Mock;
  let statusMock: jest.Mock;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn(() => mockResponse as Response);
    mockRequest = {};
    mockResponse = {
      status: statusMock,
      json: jsonMock,
    } as unknown as Response;
  });

  test("check should return 200 and success status", async () => {
    await healthController.check(mockRequest as Request, mockResponse);

    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        status: "success",
        message: "Server is healthy",
      })
    );
  });
});
