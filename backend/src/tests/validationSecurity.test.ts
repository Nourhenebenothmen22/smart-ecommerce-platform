import { productSchema, productUpdateSchema } from "../validators/product.schema.js";
import { registerSchema } from "../validators/auth.schema.js";

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
      password: "password123",
    }).success).toBe(true);
  });
});
