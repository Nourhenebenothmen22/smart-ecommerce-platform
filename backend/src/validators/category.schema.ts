import { z } from 'zod';

export const categorySchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  image_url: z.string().url().optional(),
});

export const categoryIdSchema = z.object({
  id: z.string().regex(/^\d+$/).transform(Number),
});
