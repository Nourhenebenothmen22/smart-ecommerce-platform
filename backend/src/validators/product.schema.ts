import { z } from 'zod';

export const productSchema = z.object({
  title: z.string().min(1, 'Title is required').max(255),
  slug: z.string().max(280).optional(),
  description: z.string().min(1, 'Description is required'),
  brand: z.string().min(1, 'Brand is required').max(120),
  category_id: z.number().int().positive('Category ID must be a positive integer'),
  subcategory_id: z.number().int().positive('Subcategory ID must be a positive integer'),
  price: z.number().nonnegative('Price must be greater than or equal to 0'),
  discount_percent: z.number().int().min(0).max(100, 'Discount percent must be between 0 and 100'),
  stock: z.number().int().nonnegative('Stock must be at least 0'),
  thumbnail: z.string().url('Invalid thumbnail URL').optional(),
  images: z.array(z.string().url('Invalid image URL')).optional(),
  tags: z.array(z.string()).optional(),
  is_active: z.boolean().default(true),
});

export const productIdSchema = z.object({
  id: z.coerce.number().int().positive('Product ID must be a positive integer'),
});
