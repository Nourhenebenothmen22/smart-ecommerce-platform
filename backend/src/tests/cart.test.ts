import { jest } from "@jest/globals";
import { cartController } from "../controllers/cart.controller.js";
import { cartService } from "../services/cart.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/cart.service.js", () => ({
  cartService: {
    getCart: jest.fn<any>(),
    addItem: jest.fn<any>(),
    updateItemQuantity: jest.fn<any>(),
    removeItem: jest.fn<any>(),
  },
}));

describe("CartController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: { id: 1, role: "customer", email: "test@example.com" } });
    jest.clearAllMocks();
  });

  describe("getCart", () => {
    test("returns cart items for current user", async () => {
      const items = [{ id: 1, product_id: 10, quantity: 2, title: "Phone" }];
      (cartService.getCart as any).mockResolvedValue(items);

      await cartController.getCart(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(cartService.getCart).toHaveBeenCalledWith(1);
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
      expect(ctx.jsonMock).toHaveBeenCalledWith(expect.objectContaining({ success: true, data: items }));
    });

    test("forwards service errors", async () => {
      const error = new Error("DB error");
      (cartService.getCart as any).mockRejectedValue(error);

      await cartController.getCart(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(ctx.mockNext).toHaveBeenCalledWith(error);
    });
  });

  describe("addItem", () => {
    test("adds item to cart", async () => {
      ctx.mockRequest.body = { product_id: 10, quantity: 1 };
      const item = { id: 1, product_id: 10, quantity: 1 };
      (cartService.addItem as any).mockResolvedValue(item);

      await cartController.addItem(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(cartService.addItem).toHaveBeenCalledWith(1, 10, 1);
      expect(ctx.statusMock).toHaveBeenCalledWith(201);
    });
  });

  describe("updateItem", () => {
    test("updates cart item quantity", async () => {
      ctx.mockRequest.params = { productId: "10" };
      ctx.mockRequest.body = { quantity: 3 };
      const item = { id: 1, product_id: 10, quantity: 3 };
      (cartService.updateItemQuantity as any).mockResolvedValue(item);

      await cartController.updateItem(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(cartService.updateItemQuantity).toHaveBeenCalledWith(1, 10, 3);
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });
  });

  describe("removeItem", () => {
    test("removes item from cart", async () => {
      ctx.mockRequest.params = { productId: "10" };
      (cartService.removeItem as any).mockResolvedValue(undefined);

      await cartController.removeItem(ctx.mockRequest as Request, ctx.mockResponse as Response, ctx.mockNext);

      expect(cartService.removeItem).toHaveBeenCalledWith(1, 10);
      expect(ctx.statusMock).toHaveBeenCalledWith(200);
    });
  });
});
