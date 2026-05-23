import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";
import { hashPassword, comparePassword } from "../utils/password.js";
import jwt from "jsonwebtoken";
import { env } from "../config/env.js";

export class AuthService {
  async register(data: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }) {
    // Check email uniqueness
    const existing = await pool.query("SELECT id FROM users WHERE email = $1", [data.email]);
    if (existing.rows.length > 0) {
      throw new AppError("Email already registered", StatusCodes.CONFLICT);
    }

    const password_hash = await hashPassword(data.password);

    const result = await pool.query(
      `INSERT INTO users (first_name, last_name, email, password_hash, role)
       VALUES ($1, $2, $3, $4, 'customer')
       RETURNING id, first_name, last_name, email, phone, address_line, city, postal_code, country, role, is_active, token_version, created_at, updated_at`,
      [data.first_name, data.last_name, data.email, password_hash]
    );

    const { token_version, ...user } = result.rows[0];
    const token = this.signToken({ ...user, token_version });
    return { user, token };
  }

  async login(email: string, password: string) {
    const result = await pool.query(
      `SELECT id, first_name, last_name, email, phone, address_line, city, postal_code, country,
              role, is_active, token_version, password_hash, created_at, updated_at
       FROM users WHERE email = $1`,
      [email]
    );
    if (result.rows.length === 0) {
      throw new AppError("Invalid email or password", StatusCodes.UNAUTHORIZED);
    }

    const user = result.rows[0];

    if (!user.is_active) {
      throw new AppError("Account is deactivated", StatusCodes.FORBIDDEN);
    }

    const isMatch = await comparePassword(password, user.password_hash);
    if (!isMatch) {
      throw new AppError("Invalid email or password", StatusCodes.UNAUTHORIZED);
    }

    // Remove password_hash before returning
    const { password_hash: _, token_version, ...safeUser } = user;
    const token = this.signToken({ ...safeUser, token_version });
    return { user: safeUser, token };
  }

  async revokeUserTokens(userId: number) {
    await pool.query(
      "UPDATE users SET token_version = token_version + 1, updated_at = NOW() WHERE id = $1",
      [userId]
    );
  }

  private signToken(user: { id: number; role: string; email: string; token_version: number }) {
    return jwt.sign(
      { id: user.id, role: user.role, email: user.email, tokenVersion: user.token_version },
      env.JWT_SECRET,
      { expiresIn: env.JWT_EXPIRES_IN as any }
    );
  }
}

export const authService = new AuthService();
