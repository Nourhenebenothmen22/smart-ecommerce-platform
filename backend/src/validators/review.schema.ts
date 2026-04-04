import { z } from 'zod';

export const reviewSchema = z.object({
  product_id: z.coerce.number().int().positive('Product ID must be a positive integer'),
  rating: z.coerce.number().int().min(1).max(5),
  comment: z.string().max(1000).optional(),
});

export const reviewIdSchema = z.object({
  id: z.coerce.number().int().positive('Review ID must be a positive integer'),
});

export const productIdSchema = z.object({
  id: z.coerce.number().int().positive('Product ID must be a positive integer'),
});
