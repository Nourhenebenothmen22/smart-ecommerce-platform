import { jest } from "@jest/globals";
import { orderController } from "../controllers/order.controller.js";
import { orderService } from "../services/order.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/order.service.js", () => {
  return {
    orderService: {
      createOrder: jest.fn<any>(),
      getMyOrders: jest.fn<any>(),
      getAllOrders: jest.fn<any>(),
      getOrderById: jest.fn<any>(),
      updateStatus: jest.fn<any>(),
      deleteOrder: jest.fn<any>(),
    },
  };
});

describe("OrderController Tests", () => {
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
      body: {},
      user: { id: 10, email: "user@example.com", role: "customer" },
    };
    mockResponse = {
      status: statusMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("createOrder should call orderService.createOrder", async () => {
    mockRequest.body = { items: [{ product_id: 1, quantity: 2 }], payment_method: "stripe" };
    (orderService.createOrder as any).mockResolvedValue({ id: 99 });

    await orderController.createOrder(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.createOrder).toHaveBeenCalledWith(10, mockRequest.body.items, "stripe");
    expect(statusMock).toHaveBeenCalledWith(201);
  });

  test("getMyOrders should get customer's orders", async () => {
    (orderService.getMyOrders as any).mockResolvedValue([{ id: 99 }]);

    await orderController.getMyOrders(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.getMyOrders).toHaveBeenCalledWith(10);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getAllOrders should get all orders", async () => {
    (orderService.getAllOrders as any).mockResolvedValue([]);

    await orderController.getAllOrders(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.getAllOrders).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getOrderById should return details", async () => {
    mockRequest.params = { id: "99" };
    (orderService.getOrderById as any).mockResolvedValue({ id: 99 });

    await orderController.getOrderById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.getOrderById).toHaveBeenCalledWith(99, 10, "customer");
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("updateOrderStatus should update order status", async () => {
    mockRequest.params = { id: "99" };
    mockRequest.body = { status: "processing" };
    (orderService.updateStatus as any).mockResolvedValue({ id: 99, status: "processing" });

    await orderController.updateOrderStatus(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.updateStatus).toHaveBeenCalledWith(99, "processing");
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteOrder should call deleteOrder", async () => {
    mockRequest.params = { id: "99" };
    (orderService.deleteOrder as any).mockResolvedValue(undefined);

    await orderController.deleteOrder(mockRequest as Request, mockResponse as Response, mockNext);

    expect(orderService.deleteOrder).toHaveBeenCalledWith(99);
    expect(statusMock).toHaveBeenCalledWith(200);
  });
});
