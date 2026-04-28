import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export class CategoryService {
  async getAll() {
    const result = await pool.query("SELECT * FROM categories ORDER BY name ASC");
    return result.rows;
  }

  async getById(id: number) {
    const result = await pool.query("SELECT * FROM categories WHERE id = $1", [id]);
    if (result.rows.length === 0) {
      throw new AppError("Category not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async create(data: { name: string; slug?: string; description?: string }) {
    const slug = data.slug || data.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

    const result = await pool.query(
      `INSERT INTO categories (name, slug, description)
       VALUES ($1, $2, $3)
       RETURNING *`,
      [data.name, slug, data.description || null]
    );
    return result.rows[0];
  }

  async update(id: number, data: Record<string, any>) {
    const allowedFields = ["name", "slug", "description"];
    const updates: string[] = [];
    const values: any[] = [];
    let idx = 1;

    for (const field of allowedFields) {
      if (data[field] !== undefined) {
        updates.push(`${field} = $${idx}`);
        values.push(data[field]);
        idx++;
      }
    }

    if (updates.length === 0) {
      throw new AppError("No valid fields to update", StatusCodes.BAD_REQUEST);
    }

    values.push(id);
    const result = await pool.query(
      `UPDATE categories SET ${updates.join(", ")} WHERE id = $${idx} RETURNING *`,
      values
    );

    if (result.rows.length === 0) {
      throw new AppError("Category not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async delete(id: number) {
    // Check for linked subcategories
    const subcats = await pool.query("SELECT id FROM subcategories WHERE category_id = $1 LIMIT 1", [id]);
    if (subcats.rows.length > 0) {
      throw new AppError("Cannot delete category: has linked subcategories", StatusCodes.CONFLICT);
    }

    // Check for linked products
    const products = await pool.query("SELECT id FROM products WHERE category_id = $1 LIMIT 1", [id]);
    if (products.rows.length > 0) {
      throw new AppError("Cannot delete category: has linked products", StatusCodes.CONFLICT);
    }

    const result = await pool.query("DELETE FROM categories WHERE id = $1 RETURNING id", [id]);
    if (result.rows.length === 0) {
      throw new AppError("Category not found", StatusCodes.NOT_FOUND);
    }
  }
}

export const categoryService = new CategoryService();
