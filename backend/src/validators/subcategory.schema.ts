import { z } from 'zod';

export const subcategorySchema = z.object({
  category_id: z.number().int().positive('Category ID must be a positive integer'),
  name: z.string().min(1, 'Name is required').max(120),
  slug: z.string().min(1, 'Slug is required').max(140),
  description: z.string().max(255).optional(),
});

export const subcategoryIdSchema = z.object({
  id: z.coerce.number().int().positive('Subcategory ID must be a positive integer'),
});
