import { jest } from "@jest/globals";
import { userController } from "../controllers/user.controller.js";
import { userService } from "../services/user.service.js";
import { Request, Response, NextFunction } from "express";

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
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = { params: {}, body: {}, user: { id: 100, role: "customer", email: "me@example.com" } };
    mockResponse = { status: statusMock };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getMe returns authenticated user profile", async () => {
    const profile = { id: 100, email: "me@example.com" };
    (userService.getProfile as any).mockResolvedValue(profile);

    await userController.getMe(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.getProfile).toHaveBeenCalledWith(100);
    expect(statusMock).toHaveBeenCalledWith(200);
    expect(jsonMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, data: profile })
    );
  });

  test("getAllUsers retrieves all users (admin)", async () => {
    const users = [{ id: 1 }, { id: 2 }];
    (userService.getAllUsers as any).mockResolvedValue(users);

    await userController.getAllUsers(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.getAllUsers).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getUserById retrieves user by id (admin)", async () => {
    mockRequest.params = { id: "2" };
    const user = { id: 2 };
    (userService.getUserById as any).mockResolvedValue(user);

    await userController.getUserById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.getUserById).toHaveBeenCalledWith(2);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("forwards errors to next handler", async () => {
    const error = new Error("User not found");
    (userService.getProfile as any).mockRejectedValue(error);

    await userController.getMe(mockRequest as Request, mockResponse as Response, mockNext);

    expect(mockNext).toHaveBeenCalledWith(error);
  });
});
