import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";

export class AuthController {
  async register(req: Request, res: Response, next: NextFunction) {
    try {
      // Logic will be implemented in the Authservice
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "Register not implemented yet");
    } catch (error) {
      next(error);
    }
  }

  async login(req: Request, res: Response, next: NextFunction) {
    try {
      // Logic will be implemented in the Authservice
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "Login not implemented yet");
    } catch (error) {
      next(error);
    }
  }

  async logout(req: Request, res: Response, next: NextFunction) {
    try {
      // Logic will be implemented in the Authservice
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "Logout not implemented yet");
    } catch (error) {
      next(error);
    }
  }
}

export const authController = new AuthController();
