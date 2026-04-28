import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { orderService } from "../services/order.service.js";

export class OrderController {
  async createOrder(req: Request, res: Response, next: NextFunction) {
    try {
      const order = await orderService.createOrder(req.user!.id, req.body.items, req.body.payment_method);
      sendResponse(res, StatusCodes.CREATED, "Order created", order);
    } catch (error) { next(error); }
  }

  async getMyOrders(req: Request, res: Response, next: NextFunction) {
    try {
      const orders = await orderService.getMyOrders(req.user!.id);
      sendResponse(res, StatusCodes.OK, "Orders retrieved", orders);
    } catch (error) { next(error); }
  }

  async getAllOrders(_req: Request, res: Response, next: NextFunction) {
    try {
      const orders = await orderService.getAllOrders();
      sendResponse(res, StatusCodes.OK, "All orders retrieved", orders);
    } catch (error) { next(error); }
  }

  async getOrderById(req: Request, res: Response, next: NextFunction) {
    try {
      const order = await orderService.getOrderById(Number(req.params.id), req.user!.id, req.user!.role);
      sendResponse(res, StatusCodes.OK, "Order retrieved", order);
    } catch (error) { next(error); }
  }

  async updateOrderStatus(req: Request, res: Response, next: NextFunction) {
    try {
      const order = await orderService.updateStatus(Number(req.params.id), req.body.status);
      sendResponse(res, StatusCodes.OK, "Order status updated", order);
    } catch (error) { next(error); }
  }

  async deleteOrder(req: Request, res: Response, next: NextFunction) {
    try {
      await orderService.deleteOrder(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "Order deleted");
    } catch (error) { next(error); }
  }
}

export const orderController = new OrderController();
