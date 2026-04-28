import { z } from 'zod';

export const reviewSchema = z.object({
  product_id: z.coerce.number().int().positive('Product ID must be a positive integer'),
  rating: z.coerce.number().int().min(1).max(5),
  review_text: z.string().min(1, 'Review text is required').max(2000),
});

export const updateReviewSchema = z.object({
  rating: z.coerce.number().int().min(1).max(5).optional(),
  review_text: z.string().min(1).max(2000).optional(),
});

export const reviewIdSchema = z.object({
  id: z.coerce.number().int().positive('Review ID must be a positive integer'),
});

export const productIdSchema = z.object({
  productId: z.coerce.number().int().positive('Product ID must be a positive integer'),
});

// Backward compat for old route (review.route uses :id for product)
export const productIdSchemaLegacy = z.object({
  id: z.coerce.number().int().positive('Product ID must be a positive integer'),
});
