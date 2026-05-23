import { jest } from "@jest/globals";
import { Request, Response, NextFunction } from "express";
import { categoryController } from "../controllers/category.controller.js";
import { productController } from "../controllers/product.controller.js";
import { orderController } from "../controllers/order.controller.js";
import { reviewController } from "../controllers/review.controller.js";
import { userController } from "../controllers/user.controller.js";
import { categoryService } from "../services/category.service.js";
import { productService } from "../services/product.service.js";
import { orderService } from "../services/order.service.js";
import { reviewService } from "../services/review.service.js";
import { userService } from "../services/user.service.js";

jest.mock("../services/category.service.js", () => ({
  categoryService: {
    create: jest.fn<any>(),
    getAll: jest.fn<any>(),
    getById: jest.fn<any>(),
    update: jest.fn<any>(),
    delete: jest.fn<any>(),
  },
}));

jest.mock("../services/product.service.js", () => ({
  productService: {
    createProduct: jest.fn<any>(),
    getAllProducts: jest.fn<any>(),
    getProductById: jest.fn<any>(),
    updateProduct: jest.fn<any>(),
    deleteProduct: jest.fn<any>(),
  },
}));

jest.mock("../services/order.service.js", () => ({
  orderService: {
    createOrder: jest.fn<any>(),
    getMyOrders: jest.fn<any>(),
    getOrderById: jest.fn<any>(),
    updateStatus: jest.fn<any>(),
    deleteOrder: jest.fn<any>(),
  },
}));

jest.mock("../services/review.service.js", () => ({
  reviewService: {
    create: jest.fn<any>(),
    getByProductId: jest.fn<any>(),
    update: jest.fn<any>(),
    delete: jest.fn<any>(),
  },
}));

jest.mock("../services/user.service.js", () => ({
  userService: {
    getProfile: jest.fn<any>(),
    updateProfile: jest.fn<any>(),
    updateRole: jest.fn<any>(),
    updateStatus: jest.fn<any>(),
    deleteUser: jest.fn<any>(),
  },
}));

function mockResponse() {
  const res = {
    status: jest.fn(),
    json: jest.fn(),
  } as unknown as Response;
  (res.status as jest.Mock).mockReturnValue(res);
  return res;
}

describe("CRUD controller flows", () => {
  let next: NextFunction;

  beforeEach(() => {
    jest.clearAllMocks();
    next = jest.fn();
  });

  test("category CRUD maps requests to service operations", async () => {
    const res = mockResponse();
    (categoryService.create as any).mockResolvedValue({ id: 1, name: "Phones" });
    (categoryService.update as any).mockResolvedValue({ id: 1, name: "Smartphones" });
    (categoryService.delete as any).mockResolvedValue(undefined);

    await categoryController.createCategory({ body: { name: "Phones" } } as Request, res, next);
    await categoryController.updateCategory({ params: { id: "1" }, body: { name: "Smartphones" } } as unknown as Request, res, next);
    await categoryController.deleteCategory({ params: { id: "1" } } as unknown as Request, res, next);

    expect(categoryService.create).toHaveBeenCalledWith({ name: "Phones" });
    expect(categoryService.update).toHaveBeenCalledWith(1, { name: "Smartphones" });
    expect(categoryService.delete).toHaveBeenCalledWith(1);
    expect(res.status).toHaveBeenCalledWith(201);
    expect(res.status).toHaveBeenCalledWith(200);
  });

  test("product CRUD handles create, update, and soft delete messages", async () => {
    const res = mockResponse();
    (productService.createProduct as any).mockResolvedValue({ id: 10, title: "Phone" });
    (productService.updateProduct as any).mockResolvedValue({ id: 10, price: 450 });
    (productService.deleteProduct as any).mockResolvedValue({ soft_deleted: true });

    await productController.createProduct({ body: { title: "Phone" } } as Request, res, next);
    await productController.updateProduct({ params: { id: "10" }, body: { price: 450 } } as unknown as Request, res, next);
    await productController.deleteProduct({ params: { id: "10" } } as unknown as Request, res, next);

    expect(productService.createProduct).toHaveBeenCalledWith({ title: "Phone" });
    expect(productService.updateProduct).toHaveBeenCalledWith(10, { price: 450 });
    expect(productService.deleteProduct).toHaveBeenCalledWith(10);
    expect(res.json).toHaveBeenCalledWith(expect.objectContaining({ message: "Product deactivated (linked to orders)" }));
  });

  test("order CRUD uses authenticated user context for customer operations", async () => {
    const res = mockResponse();
    const user = { id: 7, role: "customer", email: "customer@example.com" };
    (orderService.createOrder as any).mockResolvedValue({ id: 99 });
    (orderService.getOrderById as any).mockResolvedValue({ id: 99, user_id: 7 });
    (orderService.updateStatus as any).mockResolvedValue({ id: 99, status: "processing" });

    await orderController.createOrder({ user, body: { items: [{ product_id: 1, quantity: 2 }], payment_method: "card" } } as Request, res, next);
    await orderController.getOrderById({ user, params: { id: "99" } } as unknown as Request, res, next);
    await orderController.updateOrderStatus({ params: { id: "99" }, body: { status: "processing" } } as unknown as Request, res, next);

    expect(orderService.createOrder).toHaveBeenCalledWith(7, [{ product_id: 1, quantity: 2 }], "card");
    expect(orderService.getOrderById).toHaveBeenCalledWith(99, 7, "customer");
    expect(orderService.updateStatus).toHaveBeenCalledWith(99, "processing");
  });

  test("review CRUD enforces owner or admin context through service arguments", async () => {
    const res = mockResponse();
    const user = { id: 7, role: "customer", email: "customer@example.com" };
    (reviewService.create as any).mockResolvedValue({ id: 5 });
    (reviewService.update as any).mockResolvedValue({ id: 5, rating: 4 });
    (reviewService.delete as any).mockResolvedValue(undefined);

    await reviewController.addReview({ user, body: { product_id: 1, rating: 5, review_text: "Great" } } as Request, res, next);
    await reviewController.updateReview({ user, params: { id: "5" }, body: { rating: 4 } } as unknown as Request, res, next);
    await reviewController.deleteReview({ user, params: { id: "5" } } as unknown as Request, res, next);

    expect(reviewService.create).toHaveBeenCalledWith(7, { product_id: 1, rating: 5, review_text: "Great" });
    expect(reviewService.update).toHaveBeenCalledWith(5, 7, "customer", { rating: 4 });
    expect(reviewService.delete).toHaveBeenCalledWith(5, 7, "customer");
  });

  test("user profile and admin mutations use authenticated and target ids correctly", async () => {
    const res = mockResponse();
    const user = { id: 7, role: "admin", email: "admin@example.com" };
    (userService.updateProfile as any).mockResolvedValue({ id: 7, city: "Tunis" });
    (userService.updateRole as any).mockResolvedValue({ id: 8, role: "manager" });
    (userService.updateStatus as any).mockResolvedValue({ id: 8, is_active: false });
    (userService.deleteUser as any).mockResolvedValue(undefined);

    await userController.updateMe({ user, body: { city: "Tunis" } } as Request, res, next);
    await userController.updateRole({ params: { id: "8" }, body: { role: "manager" } } as unknown as Request, res, next);
    await userController.updateStatus({ params: { id: "8" }, body: { is_active: false } } as unknown as Request, res, next);
    await userController.deleteUser({ params: { id: "8" } } as unknown as Request, res, next);

    expect(userService.updateProfile).toHaveBeenCalledWith(7, { city: "Tunis" });
    expect(userService.updateRole).toHaveBeenCalledWith(8, "manager");
    expect(userService.updateStatus).toHaveBeenCalledWith(8, false);
    expect(userService.deleteUser).toHaveBeenCalledWith(8);
  });
});
