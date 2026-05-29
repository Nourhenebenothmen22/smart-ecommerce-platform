import { jest } from "@jest/globals";
import { healthController } from "../controllers/health.controller.js";
import { Request, Response } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

describe("HealthController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: null });
    jest.clearAllMocks();
  });

  test("check returns 200 with healthy status", async () => {
    await healthController.check(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response
    );

    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({
        status: "success",
        message: "Server is healthy",
        timestamp: expect.any(String),
      })
    );
  });
});
