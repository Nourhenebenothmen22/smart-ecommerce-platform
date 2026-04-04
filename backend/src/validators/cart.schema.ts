import { z } from 'zod';

export const cartItemSchema = z.object({
  product_id: z.number().int().positive('Product ID must be a positive integer'),
  quantity: z.number().int().min(1, 'Quantity must be at least 1'),
});
