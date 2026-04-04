import { z } from 'zod';

export const paymentSchema = z.object({
  order_id: z.number().int().positive('Order ID must be a positive integer'),
  amount: z.number().positive('Amount must be greater than 0'),
  payment_method: z.string().min(1, 'Payment method is required').max(50),
  status: z.enum(['pending', 'paid', 'failed', 'refunded']).default('pending'),
  transaction_ref: z.string().max(255).optional(),
});
