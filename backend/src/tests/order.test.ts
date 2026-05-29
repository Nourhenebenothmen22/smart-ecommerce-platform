import { jest } from "@jest/globals";
import { orderController } from "../controllers/order.controller.js";
import { orderService } from "../services/order.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/order.service.js", () => ({
  orderService: {
    createOrder: jest.fn<any>(),
    getMyOrders: jest.fn<any>(),
    getAllOrders: jest.fn<any>(),
    getOrderById: jest.fn<any>(),
    updateStatus: jest.fn<any>(),
    deleteOrder: jest.fn<any>(),
  },
}));

describe("OrderController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: { id: 10, role: "customer", email: "user@example.com" } });
    jest.clearAllMocks();
  });

  test("getMyOrders retrieves authenticated user orders", async () => {
    const orders = [{ id: 99 }];
    (orderService.getMyOrders as any).mockResolvedValue(orders);

    await orderController.getMyOrders(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(orderService.getMyOrders).toHaveBeenCalledWith(10);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: orders })
    );
  });

  test("getAllOrders retrieves all orders (admin)", async () => {
    const orders = [{ id: 99 }];
    (orderService.getAllOrders as any).mockResolvedValue(orders);

    await orderController.getAllOrders(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(orderService.getAllOrders).toHaveBeenCalled();
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteOrder cancels order", async () => {
    ctx.mockRequest.params = { id: "99" };
    (orderService.deleteOrder as any).mockResolvedValue(undefined);

    await orderController.deleteOrder(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(orderService.deleteOrder).toHaveBeenCalledWith(99);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("Order service error");
    (orderService.getMyOrders as any).mockRejectedValue(error);

    await orderController.getMyOrders(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
