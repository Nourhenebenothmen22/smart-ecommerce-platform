import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export class ReviewService {
  async getAll(page = 1, limit = 20) {
    const safeLimit = Math.min(limit, 100);
    const offset = (page - 1) * safeLimit;
    const countR = await pool.query("SELECT COUNT(*) FROM reviews");
    const total = parseInt(countR.rows[0].count, 10);
    const r = await pool.query(
      `SELECT r.*, p.title AS product_title, u.first_name, u.last_name, u.email
       FROM reviews r
       LEFT JOIN products p ON p.id = r.product_id
       LEFT JOIN users u ON u.id = r.user_id
       ORDER BY r.created_at DESC
       LIMIT $1 OFFSET $2`,
      [safeLimit, offset]
    );
    return { reviews: r.rows, pagination: { page, limit: safeLimit, total, totalPages: Math.ceil(total / safeLimit) } };
  }

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
    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      // 1. Verify product exists
      const prod = await client.query("SELECT id FROM products WHERE id=$1", [data.product_id]);
      if (prod.rows.length === 0) throw new AppError("Product not found", StatusCodes.NOT_FOUND);

      // 2. Check uniqueness (user can review a product only once)
      const existing = await client.query("SELECT id FROM reviews WHERE user_id=$1 AND product_id=$2", [userId, data.product_id]);
      if (existing.rows.length > 0) throw new AppError("You have already reviewed this product", StatusCodes.CONFLICT);

      // 3. Check for verified purchase
      const purchase = await client.query(
        "SELECT oi.id FROM order_items oi JOIN orders o ON o.id = oi.order_id WHERE o.user_id = $1 AND oi.product_id = $2 AND o.status = 'delivered' LIMIT 1",
        [userId, data.product_id]
      );
      const isVerified = purchase.rows.length > 0;

      // 4. Create review
      const res = await client.query(
        `INSERT INTO reviews (product_id, user_id, rating, review_text, verified_purchase) VALUES ($1,$2,$3,$4,$5) RETURNING *`,
        [data.product_id, userId, data.rating, data.review_text, isVerified]
      );

      // 5. Log ML interaction
      await client.query(
        "INSERT INTO user_interactions (user_id, product_id, interaction_type, interaction_value) VALUES ($1,$2,'review',$3)",
        [userId, data.product_id, data.rating]
      );

      // 6. Recalculate rating
      await this.recalculateProductRating(data.product_id, client);

      await client.query("COMMIT");
      return res.rows[0];
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }
  }

  async update(reviewId: number, userId: number, role: string, data: { rating?: number; review_text?: string }) {
    const review = await pool.query("SELECT * FROM reviews WHERE id=$1", [reviewId]);
    if (review.rows.length === 0) throw new AppError("Review not found", StatusCodes.NOT_FOUND);
    if (review.rows[0].user_id !== userId && role !== "admin") {
      throw new AppError("Not authorized to update this review", StatusCodes.FORBIDDEN);
    }

    const client = await pool.connect();
    try {
      await client.query("BEGIN");
      const ups: string[] = []; const vals: any[] = []; let idx = 1;
      if (data.rating !== undefined) { ups.push(`rating=$${idx}`); vals.push(data.rating); idx++; }
      if (data.review_text !== undefined) { ups.push(`review_text=$${idx}`); vals.push(data.review_text); idx++; }
      if (ups.length > 0) {
        vals.push(reviewId);
        const r = await client.query(`UPDATE reviews SET ${ups.join(",")} WHERE id=$${idx} RETURNING *`, vals);
        if (data.rating !== undefined) {
          await this.recalculateProductRating(review.rows[0].product_id, client);
        }
        await client.query("COMMIT");
        return r.rows[0];
      }
      await client.query("COMMIT");
      return review.rows[0];
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }
  }

  async delete(reviewId: number, userId: number, role: string) {
    const review = await pool.query("SELECT * FROM reviews WHERE id=$1", [reviewId]);
    if (review.rows.length === 0) throw new AppError("Review not found", StatusCodes.NOT_FOUND);
    if (review.rows[0].user_id !== userId && role !== "admin") {
      throw new AppError("Not authorized to delete this review", StatusCodes.FORBIDDEN);
    }

    const client = await pool.connect();
    try {
      await client.query("BEGIN");
      await client.query("DELETE FROM reviews WHERE id=$1", [reviewId]);
      await this.recalculateProductRating(review.rows[0].product_id, client);
      await client.query("COMMIT");
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }
  }

  private async recalculateProductRating(productId: number, client: any = pool) {
    await client.query(
      `UPDATE products SET
         rating_avg = COALESCE((SELECT AVG(rating)::NUMERIC(3,2) FROM reviews WHERE product_id=$1), 0),
         review_count = (SELECT COUNT(*) FROM reviews WHERE product_id=$1),
         updated_at = NOW()
       WHERE id=$1`,
      [productId]
    );
  }
}

export const reviewService = new ReviewService();
