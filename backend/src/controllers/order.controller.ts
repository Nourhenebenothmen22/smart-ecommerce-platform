import { Request, Response, NextFunction } from 'express';
import { StatusCodes } from 'http-status-codes';
import { sendResponse } from '../utils/apiResponse.js';

export class OrderController {
  async createOrder(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'CreateOrder not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async getMyOrders(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetMyOrders not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async getOrderById(req: Request, res: Response, next: NextFunction) {
    try {
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, 'GetOrderById not implemented yet');
    } catch (error) {
      next(error);
    }
  }

  async updateOrderStatus(req: Request, res: Response, next: NextFunction) {
    try {
      res.status(501).json({ message: 'Not implemented' });
    } catch (error) {
      next(error);
    }
  }
}

export const orderController = new OrderController();
