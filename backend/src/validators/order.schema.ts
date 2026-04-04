import { z } from 'zod';

export const orderStatusEnum = z.enum(['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']);
export const paymentStatusEnum = z.enum(['pending', 'paid', 'failed', 'refunded']);

export const orderSchema = z.object({
  status: orderStatusEnum.optional(),
  payment_status: paymentStatusEnum.optional(),
  user_id: z.number().int().positive('User ID must be a positive integer').optional(), // Only for admin routes
});

export const orderIdSchema = z.object({
  id: z.coerce.number().int().positive('Order ID must be a positive integer'),
});

export const orderStatusSchema = z.object({
  status: orderStatusEnum,
});
