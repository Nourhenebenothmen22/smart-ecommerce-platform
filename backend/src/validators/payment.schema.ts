import { z } from 'zod';
import { paymentMethodEnum } from './order.schema.js';

export const paymentSchema = z.object({
  order_id: z.number().int().positive('Order ID must be a positive integer'),
  amount: z.number().positive('Amount must be greater than 0'),
  payment_method: paymentMethodEnum,
  status: z.enum(['pending', 'paid', 'failed', 'refunded']).default('pending'),
  transaction_ref: z.string().max(255).optional(),
});
