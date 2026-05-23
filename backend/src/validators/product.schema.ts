import { z } from 'zod';

const jsonStringArray = z.preprocess((value) => {
  if (typeof value !== "string") return value;
  try {
    const parsed = JSON.parse(value);
    return parsed;
  } catch {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }
}, z.array(z.string()));

const booleanFromRequest = z.preprocess((value) => {
  if (value === "true") return true;
  if (value === "false") return false;
  return value;
}, z.boolean());

export const productSchema = z.object({
  title: z.string().min(1, 'Title is required').max(255),
  slug: z.string().max(280).optional(),
  description: z.string().min(1, 'Description is required'),
  brand: z.string().min(1, 'Brand is required').max(120),
  category_id: z.coerce.number().int().positive('Category ID must be a positive integer'),
  subcategory_id: z.coerce.number().int().positive('Subcategory ID must be a positive integer'),
  price: z.coerce.number().positive('Price must be greater than 0'),
  discount_percent: z.coerce.number().int().min(0).max(100).default(0),
  stock: z.coerce.number().int().nonnegative('Stock must be at least 0').default(0),
  thumbnail: z.string().optional(),
  images: jsonStringArray.optional(),
  tags: jsonStringArray.optional(),
  is_active: booleanFromRequest.default(true),
});

export const productUpdateSchema = productSchema.partial();

export const productIdSchema = z.object({
  id: z.coerce.number().int().positive('Product ID must be a positive integer'),
});

export const productQuerySchema = z.object({
  page: z.coerce.number().int().positive().optional(),
  limit: z.coerce.number().int().positive().max(100).optional(),
  search: z.string().optional(),
  category_id: z.coerce.number().int().positive().optional(),
  subcategory_id: z.coerce.number().int().positive().optional(),
  brand: z.string().optional(),
  min_price: z.coerce.number().nonnegative().optional(),
  max_price: z.coerce.number().nonnegative().optional(),
  sort_by: z.enum(['price', 'rating', 'created_at', 'title']).optional(),
  sort_order: z.enum(['asc', 'desc']).optional(),
});
