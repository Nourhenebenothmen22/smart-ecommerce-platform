import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";

export class UserController {
  async getProfile(req: Request, res: Response, next: NextFunction) {
    try {
      // Logic for retrieving a user profile
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "GetProfile not implemented yet");
    } catch (error) {
      next(error);
    }
  }

  async updateProfile(req: Request, res: Response, next: NextFunction) {
    try {
      // Logic for updating a user profile
      sendResponse(res, StatusCodes.NOT_IMPLEMENTED, "UpdateProfile not implemented yet");
    } catch (error) {
      next(error);
    }
  }
}

export const userController = new UserController();
