import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { cartService } from "../services/cart.service.js";

export class CartController {
  async getCart(req: Request, res: Response, next: NextFunction) {
    try {
      const items = await cartService.getCart(req.user!.id);
      sendResponse(res, StatusCodes.OK, "Cart retrieved", items);
    } catch (error) { next(error); }
  }

  async addItem(req: Request, res: Response, next: NextFunction) {
    try {
      const item = await cartService.addItem(req.user!.id, req.body.product_id, req.body.quantity);
      sendResponse(res, StatusCodes.CREATED, "Item added to cart", item);
    } catch (error) { next(error); }
  }

  async updateItem(req: Request, res: Response, next: NextFunction) {
    try {
      const item = await cartService.updateItemQuantity(
        req.user!.id,
        Number(req.params.productId),
        req.body.quantity
      );
      sendResponse(res, StatusCodes.OK, "Cart item updated", item);
    } catch (error) { next(error); }
  }

  async removeItem(req: Request, res: Response, next: NextFunction) {
    try {
      await cartService.removeItem(req.user!.id, Number(req.params.productId));
      sendResponse(res, StatusCodes.OK, "Item removed from cart");
    } catch (error) { next(error); }
  }
}

export const cartController = new CartController();
