import { jest } from "@jest/globals";
import { userController } from "../controllers/user.controller.js";
import { userService } from "../services/user.service.js";
import { Request, Response, NextFunction } from "express";
import { createMockExpress } from "./helpers/controller-test-setup.js";

jest.mock("../services/user.service.js", () => ({
  userService: {
    getProfile: jest.fn<any>(),
    updateProfile: jest.fn<any>(),
    getAllUsers: jest.fn<any>(),
    getUserById: jest.fn<any>(),
    updateRole: jest.fn<any>(),
    updateStatus: jest.fn<any>(),
    deleteUser: jest.fn<any>(),
  },
}));

describe("UserController", () => {
  let ctx: ReturnType<typeof createMockExpress>;

  beforeEach(() => {
    ctx = createMockExpress({ user: { id: 100, role: "customer", email: "me@example.com" } });
    jest.clearAllMocks();
  });

  test("getMe returns authenticated user profile", async () => {
    const profile = { id: 100, email: "me@example.com" };
    (userService.getProfile as any).mockResolvedValue(profile);

    await userController.getMe(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(userService.getProfile).toHaveBeenCalledWith(100);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
    expect(ctx.jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: profile })
    );
  });

  test("getAllUsers retrieves all users (admin)", async () => {
    const users = [{ id: 1 }, { id: 2 }];
    (userService.getAllUsers as any).mockResolvedValue(users);

    await userController.getAllUsers(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(userService.getAllUsers).toHaveBeenCalled();
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("getUserById retrieves user by id (admin)", async () => {
    ctx.mockRequest.params = { id: "2" };
    const user = { id: 2 };
    (userService.getUserById as any).mockResolvedValue(user);

    await userController.getUserById(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(userService.getUserById).toHaveBeenCalledWith(2);
    expect(ctx.statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("User not found");
    (userService.getProfile as any).mockRejectedValue(error);

    await userController.getMe(
      ctx.mockRequest as Request,
      ctx.mockResponse as Response,
      ctx.mockNext
    );

    expect(ctx.mockNext).toHaveBeenCalledWith(error);
  });
});
