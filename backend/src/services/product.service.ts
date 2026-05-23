import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export class ProductService {
  async getAllProducts(filters: any) {
    const page = filters.page || 1;
    const limit = Math.min(filters.limit || 20, 100);
    const offset = (page - 1) * limit;
    
    // Dynamic is_active: default to true if not specified
    const conds: string[] = [];
    const vals: any[] = [];
    let idx = 1;

    if (filters.is_active !== undefined) {
      conds.push(`p.is_active = $${idx}`);
      vals.push(filters.is_active === 'true' || filters.is_active === true);
      idx++;
    } else {
      conds.push(`p.is_active = true`);
    }

    if (filters.search) {
      conds.push(`(p.title ILIKE $${idx} OR p.brand ILIKE $${idx})`);
      vals.push(`%${filters.search}%`); idx++;
    }
    if (filters.category_id) { conds.push(`p.category_id = $${idx}`); vals.push(filters.category_id); idx++; }
    if (filters.subcategory_id) { conds.push(`p.subcategory_id = $${idx}`); vals.push(filters.subcategory_id); idx++; }
    if (filters.brand) { conds.push(`p.brand ILIKE $${idx}`); vals.push(`%${filters.brand}%`); idx++; }
    if (filters.min_price !== undefined) { conds.push(`p.price >= $${idx}`); vals.push(filters.min_price); idx++; }
    if (filters.max_price !== undefined) { conds.push(`p.price <= $${idx}`); vals.push(filters.max_price); idx++; }

    const where = conds.length > 0 ? `WHERE ${conds.join(" AND ")}` : "";
    const sorts: Record<string, string> = { price: "p.price", rating: "p.rating_avg", created_at: "p.created_at", title: "p.title" };
    const sortCol = sorts[filters.sort_by || "created_at"] || "p.created_at";
    const sortDir = filters.sort_order === "asc" ? "ASC" : "DESC";

    const countR = await pool.query(`SELECT COUNT(*) FROM products p ${where}`, vals);
    const total = parseInt(countR.rows[0].count, 10);

    const dataVals = [...vals, limit, offset];
    const result = await pool.query(
      `SELECT p.*, c.name as category_name, s.name as subcategory_name FROM products p
       LEFT JOIN categories c ON c.id = p.category_id LEFT JOIN subcategories s ON s.id = p.subcategory_id
       ${where} ORDER BY ${sortCol} ${sortDir} LIMIT $${idx} OFFSET $${idx + 1}`, dataVals
    );
    return { products: result.rows, pagination: { page, limit, total, totalPages: Math.ceil(total / limit) } };
  }

  async getProductById(id: number) {
    const r = await pool.query(
      `SELECT p.*, c.name as category_name, s.name as subcategory_name FROM products p
       LEFT JOIN categories c ON c.id = p.category_id LEFT JOIN subcategories s ON s.id = p.subcategory_id WHERE p.id = $1`, [id]
    );
    if (r.rows.length === 0) throw new AppError("Product not found", StatusCodes.NOT_FOUND);
    return r.rows[0];
  }

  async createProduct(data: any) {
    const sub = await pool.query("SELECT id FROM subcategories WHERE id = $1 AND category_id = $2", [data.subcategory_id, data.category_id]);
    if (sub.rows.length === 0) throw new AppError("Subcategory does not belong to category", StatusCodes.BAD_REQUEST);
    
    // Unique slug generation
    let slug = data.slug || data.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    const slugExists = await pool.query("SELECT id FROM products WHERE slug = $1", [slug]);
    if (slugExists.rows.length > 0) {
      slug = `${slug}-${Math.random().toString(36).substring(2, 7)}`;
    }

    const r = await pool.query(
      `INSERT INTO products (title,slug,description,brand,category_id,subcategory_id,price,discount_percent,stock,thumbnail,images,tags,is_active)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13) RETURNING *`,
      [data.title, slug, data.description, data.brand, data.category_id, data.subcategory_id, data.price,
       data.discount_percent||0, data.stock||0, data.thumbnail||"", JSON.stringify(data.images||[]), JSON.stringify(data.tags||[]), data.is_active!==undefined?data.is_active:true]
    );
    return r.rows[0];
  }

  async updateProduct(id: number, data: any) {
    const current = await pool.query("SELECT id, category_id, subcategory_id FROM products WHERE id=$1", [id]);
    if (current.rows.length === 0) throw new AppError("Product not found", StatusCodes.NOT_FOUND);

    const categoryId = data.category_id ?? current.rows[0].category_id;
    const subcategoryId = data.subcategory_id ?? current.rows[0].subcategory_id;
    const s = await pool.query(
      "SELECT id FROM subcategories WHERE id=$1 AND category_id=$2",
      [subcategoryId, categoryId]
    );
    if (s.rows.length === 0) {
      throw new AppError("Subcategory does not belong to category", StatusCodes.BAD_REQUEST);
    }

    const fields = ["title","slug","description","brand","category_id","subcategory_id","price","discount_percent","stock","thumbnail","is_active"];
    const ups: string[] = []; const vals: any[] = []; let idx = 1;
    for (const f of fields) { if (data[f] !== undefined) { ups.push(`${f}=$${idx}`); vals.push(data[f]); idx++; } }
    if (data.images !== undefined) { ups.push(`images=$${idx}`); vals.push(JSON.stringify(data.images)); idx++; }
    if (data.tags !== undefined) { ups.push(`tags=$${idx}`); vals.push(JSON.stringify(data.tags)); idx++; }
    if (ups.length === 0) throw new AppError("No valid fields to update", StatusCodes.BAD_REQUEST);
    ups.push("updated_at=NOW()"); vals.push(id);
    const r = await pool.query(`UPDATE products SET ${ups.join(",")} WHERE id=$${idx} RETURNING *`, vals);
    if (r.rows.length === 0) throw new AppError("Product not found", StatusCodes.NOT_FOUND);
    return r.rows[0];
  }

  async deleteProduct(id: number) {
    const oi = await pool.query("SELECT id FROM order_items WHERE product_id=$1 LIMIT 1", [id]);
    if (oi.rows.length > 0) {
      const r = await pool.query("UPDATE products SET is_active=false,updated_at=NOW() WHERE id=$1 RETURNING id", [id]);
      if (r.rows.length === 0) throw new AppError("Product not found", StatusCodes.NOT_FOUND);
      return { soft_deleted: true };
    }
    const r = await pool.query("DELETE FROM products WHERE id=$1 RETURNING id", [id]);
    if (r.rows.length === 0) throw new AppError("Product not found", StatusCodes.NOT_FOUND);
    return { soft_deleted: false };
  }
}

export const productService = new ProductService();
