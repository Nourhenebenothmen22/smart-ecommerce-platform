import { z } from 'zod';

export const orderStatusEnum = z.enum(['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']);
export const paymentStatusEnum = z.enum(['pending', 'paid', 'failed', 'refunded']);

export const createOrderSchema = z.object({
  items: z.array(
    z.object({
      product_id: z.number().int().positive('Product ID must be a positive integer'),
      quantity: z.number().int().min(1, 'Quantity must be at least 1'),
    })
  ).min(1, 'At least one item is required'),
  payment_method: z.string().min(1, 'Payment method is required').max(50),
});

export const orderIdSchema = z.object({
  id: z.coerce.number().int().positive('Order ID must be a positive integer'),
});

export const orderStatusSchema = z.object({
  status: orderStatusEnum,
});

// Keep backward compat
export const orderSchema = createOrderSchema;
