import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { userService } from "../services/user.service.js";

export class UserController {
  async getMe(req: Request, res: Response, next: NextFunction) {
    try {
      const user = await userService.getProfile(req.user!.id);
      sendResponse(res, StatusCodes.OK, "Profile retrieved", user);
    } catch (error) { next(error); }
  }

  async updateMe(req: Request, res: Response, next: NextFunction) {
    try {
      const user = await userService.updateProfile(req.user!.id, req.body);
      sendResponse(res, StatusCodes.OK, "Profile updated", user);
    } catch (error) { next(error); }
  }

  async getAllUsers(_req: Request, res: Response, next: NextFunction) {
    try {
      const users = await userService.getAllUsers();
      sendResponse(res, StatusCodes.OK, "Users retrieved", users);
    } catch (error) { next(error); }
  }

  async getUserById(req: Request, res: Response, next: NextFunction) {
    try {
      const user = await userService.getUserById(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "User retrieved", user);
    } catch (error) { next(error); }
  }

  async updateRole(req: Request, res: Response, next: NextFunction) {
    try {
      const user = await userService.updateRole(Number(req.params.id), req.body.role);
      sendResponse(res, StatusCodes.OK, "Role updated", user);
    } catch (error) { next(error); }
  }

  async updateStatus(req: Request, res: Response, next: NextFunction) {
    try {
      const user = await userService.updateStatus(Number(req.params.id), req.body.is_active);
      sendResponse(res, StatusCodes.OK, "Status updated", user);
    } catch (error) { next(error); }
  }

  async deleteUser(req: Request, res: Response, next: NextFunction) {
    try {
      await userService.deleteUser(Number(req.params.id));
      sendResponse(res, StatusCodes.OK, "User deactivated");
    } catch (error) { next(error); }
  }
}

export const userController = new UserController();
