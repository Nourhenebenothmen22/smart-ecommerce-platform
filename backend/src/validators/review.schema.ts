import { z } from 'zod';

export const reviewSchema = z.object({
  product_id: z.number().int().positive('Product ID must be a positive integer'),
  rating: z.number().int().min(1).max(5, 'Rating must be between 1 and 5'),
  review_text: z.string().min(1, 'Review text is required'),
  verified_purchase: z.boolean().default(false),
});
