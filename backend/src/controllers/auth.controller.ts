import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { authService } from "../services/auth.service.js";
import { env } from "../config/env.js";

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: env.NODE_ENV === "production",
  sameSite: "lax" as const,
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
};

export class AuthController {
  async register(req: Request, res: Response, next: NextFunction) {
    try {
      const { user, token } = await authService.register(req.body);
      res.cookie("access_token", token, COOKIE_OPTIONS);
      sendResponse(res, StatusCodes.CREATED, "Registration successful", { user });
    } catch (error) {
      next(error);
    }
  }

  async login(req: Request, res: Response, next: NextFunction) {
    try {
      const { user, token } = await authService.login(req.body.email, req.body.password);
      res.cookie("access_token", token, COOKIE_OPTIONS);
      sendResponse(res, StatusCodes.OK, "Login successful", { user });
    } catch (error) {
      next(error);
    }
  }

  async logout(req: Request, res: Response, next: NextFunction) {
    try {
      await authService.revokeUserTokens(req.user!.id);
      res.clearCookie("access_token", COOKIE_OPTIONS);
      sendResponse(res, StatusCodes.OK, "Logged out successfully");
    } catch (error) {
      next(error);
    }
  }
}

export const authController = new AuthController();
