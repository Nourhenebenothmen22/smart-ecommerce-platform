import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export class ReviewService {
  async getByProductId(productId: number, page = 1, limit = 20) {
    const offset = (page - 1) * limit;
    const countR = await pool.query("SELECT COUNT(*) FROM reviews WHERE product_id=$1", [productId]);
    const total = parseInt(countR.rows[0].count, 10);
    const r = await pool.query(
      `SELECT r.*, u.first_name, u.last_name FROM reviews r
       LEFT JOIN users u ON u.id = r.user_id
       WHERE r.product_id=$1 ORDER BY r.created_at DESC LIMIT $2 OFFSET $3`,
      [productId, limit, offset]
    );
    return { reviews: r.rows, pagination: { page, limit, total, totalPages: Math.ceil(total / limit) } };
  }

  async create(userId: number, data: { product_id: number; rating: number; review_text: string }) {
    // Verify product exists
    const prod = await pool.query("SELECT id FROM products WHERE id=$1", [data.product_id]);
    if (prod.rows.length === 0) throw new AppError("Product not found", StatusCodes.NOT_FOUND);

    // Check uniqueness (user can review a product only once)
    const existing = await pool.query("SELECT id FROM reviews WHERE user_id=$1 AND product_id=$2", [userId, data.product_id]);
    if (existing.rows.length > 0) throw new AppError("You have already reviewed this product", StatusCodes.CONFLICT);

    const r = await pool.query(
      `INSERT INTO reviews (product_id, user_id, rating, review_text) VALUES ($1,$2,$3,$4) RETURNING *`,
      [data.product_id, userId, data.rating, data.review_text]
    );
    await this.recalculateProductRating(data.product_id);
    return r.rows[0];
  }

  async update(reviewId: number, userId: number, role: string, data: { rating?: number; review_text?: string }) {
    const review = await pool.query("SELECT * FROM reviews WHERE id=$1", [reviewId]);
    if (review.rows.length === 0) throw new AppError("Review not found", StatusCodes.NOT_FOUND);
    if (review.rows[0].user_id !== userId && role !== "admin") {
      throw new AppError("Not authorized to update this review", StatusCodes.FORBIDDEN);
    }
    const ups: string[] = []; const vals: any[] = []; let idx = 1;
    if (data.rating !== undefined) { ups.push(`rating=$${idx}`); vals.push(data.rating); idx++; }
    if (data.review_text !== undefined) { ups.push(`review_text=$${idx}`); vals.push(data.review_text); idx++; }
    if (ups.length === 0) throw new AppError("No fields to update", StatusCodes.BAD_REQUEST);
    vals.push(reviewId);
    const r = await pool.query(`UPDATE reviews SET ${ups.join(",")} WHERE id=$${idx} RETURNING *`, vals);
    await this.recalculateProductRating(review.rows[0].product_id);
    return r.rows[0];
  }

  async delete(reviewId: number, userId: number, role: string) {
    const review = await pool.query("SELECT * FROM reviews WHERE id=$1", [reviewId]);
    if (review.rows.length === 0) throw new AppError("Review not found", StatusCodes.NOT_FOUND);
    if (review.rows[0].user_id !== userId && role !== "admin") {
      throw new AppError("Not authorized to delete this review", StatusCodes.FORBIDDEN);
    }
    await pool.query("DELETE FROM reviews WHERE id=$1", [reviewId]);
    await this.recalculateProductRating(review.rows[0].product_id);
  }

  private async recalculateProductRating(productId: number) {
    await pool.query(
      `UPDATE products SET
         rating_avg = COALESCE((SELECT AVG(rating)::NUMERIC(3,2) FROM reviews WHERE product_id=$1), 0),
         review_count = (SELECT COUNT(*) FROM reviews WHERE product_id=$1)
       WHERE id=$1`,
      [productId]
    );
  }
}

export const reviewService = new ReviewService();
