import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { authService } from "../services/auth.service.js";
import { env } from "../config/env.js";

const DURATION_MS: Record<string, number> = {
  s: 1000,
  m: 60 * 1000,
  h: 60 * 60 * 1000,
  d: 24 * 60 * 60 * 1000,
};

export function parseJwtExpiryMs(value: string): number {
  const match = value.trim().match(/^(\d+)([smhd])$/i);
  if (!match) return 7 * DURATION_MS.d;
  return Number(match[1]) * DURATION_MS[match[2].toLowerCase()];
}

export function getCookieOptions() {
  return {
    httpOnly: true,
    secure: env.NODE_ENV === "production",
    sameSite: "lax" as const,
    maxAge: parseJwtExpiryMs(env.JWT_EXPIRES_IN),
  };
}

function getClearCookieOptions() {
  const { maxAge: _maxAge, ...options } = getCookieOptions();
  return options;
}

export class AuthController {
  async register(req: Request, res: Response, next: NextFunction) {
    try {
      const { user, token } = await authService.register(req.body);
      res.cookie("access_token", token, getCookieOptions());
      sendResponse(res, StatusCodes.CREATED, "Registration successful", { user });
    } catch (error) {
      next(error);
    }
  }

  async login(req: Request, res: Response, next: NextFunction) {
    try {
      const { user, token } = await authService.login(req.body.email, req.body.password);
      res.cookie("access_token", token, getCookieOptions());
      sendResponse(res, StatusCodes.OK, "Login successful", { user });
    } catch (error) {
      next(error);
    }
  }

  async logout(req: Request, res: Response, next: NextFunction) {
    try {
      await authService.revokeUserTokens(req.user!.id);
      res.clearCookie("access_token", getClearCookieOptions());
      sendResponse(res, StatusCodes.OK, "Logged out successfully");
    } catch (error) {
      next(error);
    }
  }
}

export const authController = new AuthController();
