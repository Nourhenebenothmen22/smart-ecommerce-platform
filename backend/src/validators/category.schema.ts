import { z } from 'zod';

export const categorySchema = z.object({
  name: z.string().min(1).max(120),
  slug: z.string().max(140).optional(),
  description: z.string().max(500).optional(),
});

export const categoryIdSchema = z.object({
  id: z.coerce.number().int().positive('Category ID must be a positive integer'),
});

export const categoryIdParamSchema = z.object({
  categoryId: z.coerce.number().int().positive('Category ID must be a positive integer'),
});
