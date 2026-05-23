import { jest } from "@jest/globals";
import { userController } from "../controllers/user.controller.js";
import { userService } from "../services/user.service.js";
import { Request, Response, NextFunction } from "express";

jest.mock("../services/user.service.js", () => {
  return {
    userService: {
      getProfile: jest.fn<any>(),
      updateProfile: jest.fn<any>(),
      getAllUsers: jest.fn<any>(),
      getUserById: jest.fn<any>(),
      updateRole: jest.fn<any>(),
      updateStatus: jest.fn<any>(),
      deleteUser: jest.fn<any>(),
    },
  };
});

describe("UserController Tests", () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: any;
  let statusMock: any;

  beforeEach(() => {
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockRequest = {
      params: {},
      body: {},
      user: { id: 100, email: "me@example.com", role: "customer" },
    };
    mockResponse = {
      status: statusMock,
    };
    mockNext = jest.fn();
    jest.clearAllMocks();
  });

  test("getMe should return my profile", async () => {
    (userService.getProfile as any).mockResolvedValue({ id: 100, email: "me@example.com" });

    await userController.getMe(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.getProfile).toHaveBeenCalledWith(100);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("updateMe should update profile", async () => {
    mockRequest.body = { first_name: "Jane" };
    (userService.updateProfile as any).mockResolvedValue({ id: 100, first_name: "Jane" });

    await userController.updateMe(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.updateProfile).toHaveBeenCalledWith(100, mockRequest.body);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getAllUsers should retrieve users", async () => {
    (userService.getAllUsers as any).mockResolvedValue([{ id: 1 }]);

    await userController.getAllUsers(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.getAllUsers).toHaveBeenCalled();
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("getUserById should retrieve user", async () => {
    mockRequest.params = { id: "2" };
    (userService.getUserById as any).mockResolvedValue({ id: 2 });

    await userController.getUserById(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.getUserById).toHaveBeenCalledWith(2);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("updateRole should modify role", async () => {
    mockRequest.params = { id: "2" };
    mockRequest.body = { role: "admin" };
    (userService.updateRole as any).mockResolvedValue({ id: 2, role: "admin" });

    await userController.updateRole(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.updateRole).toHaveBeenCalledWith(2, "admin");
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("updateStatus should update is_active", async () => {
    mockRequest.params = { id: "2" };
    mockRequest.body = { is_active: false };
    (userService.updateStatus as any).mockResolvedValue({ id: 2, is_active: false });

    await userController.updateStatus(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.updateStatus).toHaveBeenCalledWith(2, false);
    expect(statusMock).toHaveBeenCalledWith(200);
  });

  test("deleteUser should deactivate user", async () => {
    mockRequest.params = { id: "2" };
    (userService.deleteUser as any).mockResolvedValue(undefined);

    await userController.deleteUser(mockRequest as Request, mockResponse as Response, mockNext);

    expect(userService.deleteUser).toHaveBeenCalledWith(2);
    expect(statusMock).toHaveBeenCalledWith(200);
  });
});
