import { z } from 'zod';

export const userIdSchema = z.object({
  id: z.coerce.number().int().positive('ID must be a positive integer'),
});

export const updateUserSchema = z.object({
  first_name: z.string().min(1, 'First name cannot be empty').optional(),
  last_name: z.string().min(1, 'Last name cannot be empty').optional(),
  phone: z.string().max(30).regex(/^[+]?[(]?[0-9]{3}[)]?[-s.]?[0-9]{3}[-s.]?[0-9]{4,6}$/, 'Invalid phone format').optional(),
  address_line: z.string().max(255).optional(),
  city: z.string().max(120).optional(),
  postal_code: z.string().max(30).optional(),
  country: z.string().max(120).optional(),
  role: z.enum(['customer', 'admin', 'manager']).optional(),
  is_active: z.boolean().optional(),
});
