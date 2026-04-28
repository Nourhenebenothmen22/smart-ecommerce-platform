import { z } from 'zod';

export const userIdSchema = z.object({
  id: z.coerce.number().int().positive(),
});

export const updateProfileSchema = z.object({
  first_name: z.string().min(1).optional(),
  last_name: z.string().min(1).optional(),
  phone: z.string().max(30).optional(),
  address_line: z.string().max(255).optional(),
  city: z.string().max(120).optional(),
  postal_code: z.string().max(30).optional(),
  country: z.string().max(120).optional(),
});

export const updateRoleSchema = z.object({
  role: z.enum(['customer', 'admin', 'manager']),
});

export const updateStatusSchema = z.object({
  is_active: z.boolean(),
});

// Keep backward compat alias
export const updateUserSchema = updateProfileSchema;
