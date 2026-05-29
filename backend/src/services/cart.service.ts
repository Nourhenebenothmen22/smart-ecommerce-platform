import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export class CartService {
  async getCart(userId: number) {
    const r = await pool.query(
      `SELECT ci.id, ci.product_id, ci.quantity, p.title, p.price, p.final_price, p.thumbnail, p.stock, p.is_active
       FROM cart_items ci JOIN products p ON p.id = ci.product_id
       WHERE ci.user_id = $1 ORDER BY ci.created_at DESC`,
      [userId]
    );
    return r.rows;
  }

  async addItem(userId: number, productId: number, quantity: number) {
    const p = await pool.query(
      "SELECT id, is_active, stock FROM products WHERE id = $1",
      [productId]
    );
    if (p.rows.length === 0) {
      throw new AppError("Product not found", StatusCodes.NOT_FOUND);
    }
    if (!p.rows[0].is_active) {
      throw new AppError("Product is unavailable", StatusCodes.BAD_REQUEST);
    }

    const existing = await pool.query(
      "SELECT id, quantity FROM cart_items WHERE user_id = $1 AND product_id = $2",
      [userId, productId]
    );

    if (existing.rows.length > 0) {
      const newQty = existing.rows[0].quantity + quantity;
      if (newQty > p.rows[0].stock) {
        throw new AppError(
          `Insufficient stock. Available: ${p.rows[0].stock}`,
          StatusCodes.BAD_REQUEST
        );
      }
      const r = await pool.query(
        "UPDATE cart_items SET quantity = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
        [newQty, existing.rows[0].id]
      );
      return r.rows[0];
    }

    if (quantity > p.rows[0].stock) {
      throw new AppError(
        `Insufficient stock. Available: ${p.rows[0].stock}`,
        StatusCodes.BAD_REQUEST
      );
    }

    const r = await pool.query(
      "INSERT INTO cart_items (user_id, product_id, quantity) VALUES ($1, $2, $3) RETURNING *",
      [userId, productId, quantity]
    );
    return r.rows[0];
  }

  async updateItemQuantity(userId: number, productId: number, quantity: number) {
    const item = await pool.query(
      "SELECT ci.id, p.stock FROM cart_items ci JOIN products p ON p.id = ci.product_id WHERE ci.user_id = $1 AND ci.product_id = $2",
      [userId, productId]
    );
    if (item.rows.length === 0) {
      throw new AppError("Cart item not found", StatusCodes.NOT_FOUND);
    }
    if (quantity > item.rows[0].stock) {
      throw new AppError(
        `Insufficient stock. Available: ${item.rows[0].stock}`,
        StatusCodes.BAD_REQUEST
      );
    }

    const r = await pool.query(
      "UPDATE cart_items SET quantity = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
      [quantity, item.rows[0].id]
    );
    return r.rows[0];
  }

  async removeItem(userId: number, productId: number) {
    const r = await pool.query(
      "DELETE FROM cart_items WHERE user_id = $1 AND product_id = $2 RETURNING id",
      [userId, productId]
    );
    if (r.rows.length === 0) {
      throw new AppError("Cart item not found", StatusCodes.NOT_FOUND);
    }
  }
}

export const cartService = new CartService();
