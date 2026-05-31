import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { wishlistService } from "../services/wishlist.service.js";

export class WishlistController {
  async getWishlist(req: Request, res: Response, next: NextFunction) {
    try {
      const items = await wishlistService.getWishlist(req.user!.id);
      sendResponse(res, StatusCodes.OK, "Wishlist retrieved", items);
    } catch (error) { next(error); }
  }

  async addItem(req: Request, res: Response, next: NextFunction) {
    try {
      const item = await wishlistService.addItem(req.user!.id, req.body.product_id);
      sendResponse(res, StatusCodes.CREATED, "Item added to wishlist", item);
    } catch (error) { next(error); }
  }

  async removeItem(req: Request, res: Response, next: NextFunction) {
    try {
      await wishlistService.removeItem(req.user!.id, Number(req.params.productId));
      sendResponse(res, StatusCodes.OK, "Item removed from wishlist");
    } catch (error) { next(error); }
  }
}

export const wishlistController = new WishlistController();
