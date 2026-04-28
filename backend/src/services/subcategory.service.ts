import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export class SubcategoryService {
  async getAll() {
    const result = await pool.query(
      `SELECT s.*, c.name as category_name
       FROM subcategories s
       JOIN categories c ON c.id = s.category_id
       ORDER BY s.name ASC`
    );
    return result.rows;
  }

  async getById(id: number) {
    const result = await pool.query(
      `SELECT s.*, c.name as category_name
       FROM subcategories s
       JOIN categories c ON c.id = s.category_id
       WHERE s.id = $1`,
      [id]
    );
    if (result.rows.length === 0) {
      throw new AppError("Subcategory not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async getByCategoryId(categoryId: number) {
    // Verify category exists
    const cat = await pool.query("SELECT id FROM categories WHERE id = $1", [categoryId]);
    if (cat.rows.length === 0) {
      throw new AppError("Category not found", StatusCodes.NOT_FOUND);
    }

    const result = await pool.query(
      "SELECT * FROM subcategories WHERE category_id = $1 ORDER BY name ASC",
      [categoryId]
    );
    return result.rows;
  }

  async create(data: { category_id: number; name: string; slug?: string; description?: string }) {
    // Verify category exists
    const cat = await pool.query("SELECT id FROM categories WHERE id = $1", [data.category_id]);
    if (cat.rows.length === 0) {
      throw new AppError("Category not found", StatusCodes.NOT_FOUND);
    }

    const slug = data.slug || data.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

    const result = await pool.query(
      `INSERT INTO subcategories (category_id, name, slug, description)
       VALUES ($1, $2, $3, $4)
       RETURNING *`,
      [data.category_id, data.name, slug, data.description || null]
    );
    return result.rows[0];
  }

  async update(id: number, data: Record<string, any>) {
    // If category_id is being updated, verify it exists
    if (data.category_id) {
      const cat = await pool.query("SELECT id FROM categories WHERE id = $1", [data.category_id]);
      if (cat.rows.length === 0) {
        throw new AppError("Category not found", StatusCodes.NOT_FOUND);
      }
    }

    const allowedFields = ["category_id", "name", "slug", "description"];
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
      `UPDATE subcategories SET ${updates.join(", ")} WHERE id = $${idx} RETURNING *`,
      values
    );

    if (result.rows.length === 0) {
      throw new AppError("Subcategory not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async delete(id: number) {
    // Check for linked products
    const products = await pool.query("SELECT id FROM products WHERE subcategory_id = $1 LIMIT 1", [id]);
    if (products.rows.length > 0) {
      throw new AppError("Cannot delete subcategory: has linked products", StatusCodes.CONFLICT);
    }

    const result = await pool.query("DELETE FROM subcategories WHERE id = $1 RETURNING id", [id]);
    if (result.rows.length === 0) {
      throw new AppError("Subcategory not found", StatusCodes.NOT_FOUND);
    }
  }
}

export const subcategoryService = new SubcategoryService();
