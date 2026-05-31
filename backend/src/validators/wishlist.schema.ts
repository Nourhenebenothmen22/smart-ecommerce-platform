import { z } from 'zod';

export const wishlistItemSchema = z.object({
  product_id: z.coerce.number().int().positive('Product ID must be a positive integer'),
});

export const wishlistProductIdSchema = z.object({
  productId: z.coerce.number().int().positive('Product ID must be a positive integer'),
});
