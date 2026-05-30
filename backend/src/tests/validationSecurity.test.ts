import { productSchema, productUpdateSchema } from "../validators/product.schema.js";
import { registerSchema } from "../validators/auth.schema.js";
import { createOrderSchema, orderStatusEnum, paymentMethodEnum } from "../validators/order.schema.js";
import { parseJwtExpiryMs } from "../controllers/auth.controller.js";
import { isAllowedImageSignature } from "../middlewares/upload.middleware.js";

describe("validation hardening", () => {
  test("product create requires required catalog fields", () => {
    const parsed = productSchema.safeParse({ title: "Only a title" });

    expect(parsed.success).toBe(false);
  });

  test("product create accepts multipart form numeric and array values after coercion", () => {
    const parsed = productSchema.safeParse({
      title: "Phone",
      description: "A phone",
      brand: "Acme",
      category_id: "1",
      subcategory_id: "2",
      price: "499.99",
      discount_percent: "10",
      stock: "5",
      tags: '["mobile","sale"]',
      is_active: "false",
    });

    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.price).toBe(499.99);
      expect(parsed.data.tags).toEqual(["mobile", "sale"]);
      expect(parsed.data.is_active).toBe(false);
    }
  });

  test("product update validates supplied fields", () => {
    const parsed = productUpdateSchema.safeParse({ price: "-1" });

    expect(parsed.success).toBe(false);
  });

  test("registration passwords require bounded passphrases with letters and numbers", () => {
    expect(registerSchema.safeParse({
      first_name: "Ada",
      last_name: "Lovelace",
      email: "ada@example.com",
      password: "password",
    }).success).toBe(false);

    expect(registerSchema.safeParse({
      first_name: "Ada",
      last_name: "Lovelace",
      email: "ada@example.com",
      password: "Password123!",
    }).success).toBe(true);
  });

  test("order status and payment method enums are aligned with seeded data", () => {
    expect(orderStatusEnum.safeParse("completed").success).toBe(true);
    expect(orderStatusEnum.safeParse("on_hold").success).toBe(true);
    expect(paymentMethodEnum.safeParse("credit_card").success).toBe(true);
    expect(paymentMethodEnum.safeParse("apple_pay").success).toBe(true);
    expect(createOrderSchema.safeParse({
      items: [{ product_id: 1, quantity: 1 }],
      payment_method: "card",
    }).success).toBe(false);
  });

  test("jwt cookie expiry follows JWT_EXPIRES_IN duration syntax", () => {
    expect(parseJwtExpiryMs("15m")).toBe(15 * 60 * 1000);
    expect(parseJwtExpiryMs("2h")).toBe(2 * 60 * 60 * 1000);
    expect(parseJwtExpiryMs("7d")).toBe(7 * 24 * 60 * 60 * 1000);
  });

  test("uploaded image signatures require real image bytes", () => {
    expect(isAllowedImageSignature(Buffer.from([0xff, 0xd8, 0xff, 0x00]))).toBe(true);
    expect(isAllowedImageSignature(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))).toBe(true);
    expect(isAllowedImageSignature(Buffer.from("not an image"))).toBe(false);
  });
});
