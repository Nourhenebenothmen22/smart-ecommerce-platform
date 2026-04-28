import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

const SAFE_USER_COLUMNS = "id, first_name, last_name, email, phone, address_line, city, postal_code, country, role, is_active, created_at, updated_at";

export class UserService {
  async getProfile(userId: number) {
    const result = await pool.query(
      `SELECT ${SAFE_USER_COLUMNS} FROM users WHERE id = $1`,
      [userId]
    );
    if (result.rows.length === 0) {
      throw new AppError("User not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async updateProfile(userId: number, data: Record<string, any>) {
    const allowedFields = ["first_name", "last_name", "phone", "address_line", "city", "postal_code", "country"];
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

    updates.push(`updated_at = NOW()`);
    values.push(userId);

    const result = await pool.query(
      `UPDATE users SET ${updates.join(", ")} WHERE id = $${idx} RETURNING ${SAFE_USER_COLUMNS}`,
      values
    );

    if (result.rows.length === 0) {
      throw new AppError("User not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async getAllUsers() {
    const result = await pool.query(`SELECT ${SAFE_USER_COLUMNS} FROM users ORDER BY created_at DESC`);
    return result.rows;
  }

  async getUserById(id: number) {
    const result = await pool.query(`SELECT ${SAFE_USER_COLUMNS} FROM users WHERE id = $1`, [id]);
    if (result.rows.length === 0) {
      throw new AppError("User not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async updateRole(id: number, role: string) {
    const result = await pool.query(
      `UPDATE users SET role = $1, updated_at = NOW() WHERE id = $2 RETURNING ${SAFE_USER_COLUMNS}`,
      [role, id]
    );
    if (result.rows.length === 0) {
      throw new AppError("User not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async updateStatus(id: number, is_active: boolean) {
    const result = await pool.query(
      `UPDATE users SET is_active = $1, updated_at = NOW() WHERE id = $2 RETURNING ${SAFE_USER_COLUMNS}`,
      [is_active, id]
    );
    if (result.rows.length === 0) {
      throw new AppError("User not found", StatusCodes.NOT_FOUND);
    }
    return result.rows[0];
  }

  async deleteUser(id: number) {
    // Soft delete — deactivate instead of removing
    const result = await pool.query(
      `UPDATE users SET is_active = false, updated_at = NOW() WHERE id = $1 RETURNING id`,
      [id]
    );
    if (result.rows.length === 0) {
      throw new AppError("User not found", StatusCodes.NOT_FOUND);
    }
  }
}

export const userService = new UserService();
