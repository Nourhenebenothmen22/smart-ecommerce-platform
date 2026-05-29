import { jest } from "@jest/globals";
import { orderController } from "../controllers/order.controller.js";
import { orderService } from "../services/order.service.js";
import { Request, Response, NextFunction } from "express";

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
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = { params: {}, body: {}, user: { id: 10, role: "customer", email: "user@example.com" } };
    mockResponse = { status: statusMock };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getMyOrders retrieves authenticated user orders", async () => {
    const orders = [{ id: 99 }];
    (orderService.getMyOrders as any).mockResolvedValue(orders);

    await orderController.getMyOrders(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.getMyOrders).toHaveBeenCalledWith(10);
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: orders })
    );
  });

  test("getAllOrders retrieves all orders (admin)", async () => {
    const orders = [{ id: 99 }];
    (orderService.getAllOrders as any).mockResolvedValue(orders);

    await orderController.getAllOrders(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.getAllOrders).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteOrder cancels order", async () => {
    mockRequest.params = { id: "99" };
    (orderService.deleteOrder as any).mockResolvedValue(undefined);

    await orderController.deleteOrder(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.deleteOrder).toHaveBeenCalledWith(99);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("Order service error");
    (orderService.getMyOrders as any).mockRejectedValue(error);

    await orderController.getMyOrders(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mockNext).toHaveBeenCalledWith(error);
  });
});
