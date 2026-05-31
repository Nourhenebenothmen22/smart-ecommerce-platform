import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export class WishlistService {
  async getWishlist(userId: number) {
    const result = await pool.query(
      `SELECT w.id, w.product_id, w.created_at,
              p.title, p.price, p.final_price, p.thumbnail, p.stock, p.is_active,
              c.name AS category_name, s.name AS subcategory_name
       FROM wishlists w
       JOIN products p ON p.id = w.product_id
       LEFT JOIN categories c ON c.id = p.category_id
       LEFT JOIN subcategories s ON s.id = p.subcategory_id
       WHERE w.user_id = $1
       ORDER BY w.created_at DESC`,
      [userId]
    );
    return result.rows;
  }

  async addItem(userId: number, productId: number) {
    const product = await pool.query(
      "SELECT id, is_active FROM products WHERE id = $1",
      [productId]
    );
    if (product.rows.length === 0) {
      throw new AppError("Product not found", StatusCodes.NOT_FOUND);
    }
    if (!product.rows[0].is_active) {
      throw new AppError("Product is unavailable", StatusCodes.BAD_REQUEST);
    }

    const result = await pool.query(
      `INSERT INTO wishlists (user_id, product_id)
       VALUES ($1, $2)
       ON CONFLICT (user_id, product_id) DO UPDATE SET product_id = EXCLUDED.product_id
       RETURNING *`,
      [userId, productId]
    );
    return result.rows[0];
  }

  async removeItem(userId: number, productId: number) {
    const result = await pool.query(
      "DELETE FROM wishlists WHERE user_id = $1 AND product_id = $2 RETURNING id",
      [userId, productId]
    );
    if (result.rows.length === 0) {
      throw new AppError("Wishlist item not found", StatusCodes.NOT_FOUND);
    }
  }
}

export const wishlistService = new WishlistService();
