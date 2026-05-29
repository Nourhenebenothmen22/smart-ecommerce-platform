import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";
import { env } from "../config/env.js";
import type { PoolClient } from "pg";
import { logger } from "../utils/logger.js";

const ALLOWED_STATUS_TRANSITIONS: Record<string, Set<string>> = {
  pending: new Set(["pending_phone_confirmation", "processing", "cancelled", "on_hold"]),
  pending_phone_confirmation: new Set(["processing", "manual_review", "cancelled", "on_hold"]),
  manual_review: new Set(["processing", "cancelled", "on_hold"]),
  processing: new Set(["shipped", "cancelled", "refunded", "on_hold"]),
  shipped: new Set(["delivered", "refunded"]),
  delivered: new Set(["completed", "refunded"]),
  on_hold: new Set(["pending_phone_confirmation", "manual_review", "processing", "cancelled"]),
  cancelled: new Set([]),
  refunded: new Set([]),
  completed: new Set([]),
};

export class OrderService {
  async createOrder(userId: number, items: { product_id: number; quantity: number }[], payment_method: string) {
    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      // 1. Validate products & stock
      let totalAmount = 0;
      const orderItems: any[] = [];

      for (const item of items) {
        const pr = await client.query(
          "SELECT id, title, final_price, stock, is_active FROM products WHERE id=$1 FOR UPDATE",
          [item.product_id]
        );
        if (pr.rows.length === 0) throw new AppError(`Product ${item.product_id} not found`, StatusCodes.NOT_FOUND);
        const product = pr.rows[0];
        if (!product.is_active) throw new AppError(`Product "${product.title}" is unavailable`, StatusCodes.BAD_REQUEST);
        if (product.stock < item.quantity) {
          throw new AppError(`Insufficient stock for "${product.title}". Available: ${product.stock}`, StatusCodes.BAD_REQUEST);
        }
        const subtotal = parseFloat(product.final_price) * item.quantity;
        totalAmount += subtotal;
        orderItems.push({ product_id: item.product_id, product_name: product.title, unit_price: product.final_price, quantity: item.quantity, subtotal });
      }

      // 2. Create order with phone-confirmation gate
      const orderR = await client.query(
        `INSERT INTO orders (user_id, status, total_amount, payment_status) VALUES ($1,'pending_phone_confirmation',$2,'pending') RETURNING *`,
        [userId, totalAmount]
      );
      const order = orderR.rows[0];

      // 3. Create order_items & decrement stock & log interactions
      for (const oi of orderItems) {
        await client.query(
          `INSERT INTO order_items (order_id, product_id, product_name_snapshot, quantity, unit_price, subtotal) VALUES ($1,$2,$3,$4,$5,$6)`,
          [order.id, oi.product_id, oi.product_name, oi.quantity, oi.unit_price, oi.subtotal]
        );
        await client.query("UPDATE products SET stock = stock - $1, updated_at=NOW() WHERE id=$2", [oi.quantity, oi.product_id]);
        
        // Log ML Interaction
        await client.query(
          "INSERT INTO user_interactions (user_id, product_id, interaction_type, interaction_value) VALUES ($1,$2,'purchase',1)",
          [userId, oi.product_id]
        );
      }

      // 4. Create payment record
      await client.query(
        `INSERT INTO payments (order_id, payment_method, amount, status) VALUES ($1,$2,$3,'pending')`,
        [order.id, payment_method, totalAmount]
      );

      await client.query("COMMIT");

      // Auto-trigger the phone confirmation service in the background
      try {
        const webhookBaseUrl = env.WEBHOOK_BASE_URL || "http://localhost:5000";
        const { PhoneConfirmationService } = await import("./phoneConfirmation.service.js");
        const { RetellProvider } = await import("./voice/retell.provider.js");
        const phoneService = new PhoneConfirmationService(new RetellProvider());
        
        // Fire-and-forget background trigger
        phoneService.initiateCall(order.id, webhookBaseUrl).catch((err: any) => {
          logger.error({ orderId: order.id, err }, "Failed to auto-trigger voice call");
        });
      } catch (err: any) {
        logger.error({ err }, "Failed to import/initialize voice service for auto-trigger");
      }

      // Return full order with items
      return { ...order, items: orderItems };
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  async getMyOrders(userId: number) {
    const r = await pool.query(
      `SELECT o.*, json_agg(json_build_object('id',oi.id,'product_id',oi.product_id,'product_name',oi.product_name_snapshot,'quantity',oi.quantity,'unit_price',oi.unit_price,'subtotal',oi.subtotal)) as items
       FROM orders o LEFT JOIN order_items oi ON oi.order_id=o.id WHERE o.user_id=$1 GROUP BY o.id ORDER BY o.created_at DESC`,
      [userId]
    );
    return r.rows;
  }

  async getAllOrders() {
    const r = await pool.query(
      `SELECT o.*, u.first_name, u.last_name, u.email,
       json_agg(json_build_object('id',oi.id,'product_id',oi.product_id,'product_name',oi.product_name_snapshot,'quantity',oi.quantity,'unit_price',oi.unit_price,'subtotal',oi.subtotal)) as items
       FROM orders o LEFT JOIN order_items oi ON oi.order_id=o.id LEFT JOIN users u ON u.id=o.user_id GROUP BY o.id, u.first_name, u.last_name, u.email ORDER BY o.created_at DESC`
    );
    return r.rows;
  }

  async getOrderById(orderId: number, userId: number, role: string) {
    const r = await pool.query(
      `SELECT o.*, json_agg(json_build_object('id',oi.id,'product_id',oi.product_id,'product_name',oi.product_name_snapshot,'quantity',oi.quantity,'unit_price',oi.unit_price,'subtotal',oi.subtotal)) as items
       FROM orders o LEFT JOIN order_items oi ON oi.order_id=o.id WHERE o.id=$1 GROUP BY o.id`,
      [orderId]
    );
    if (r.rows.length === 0) throw new AppError("Order not found", StatusCodes.NOT_FOUND);
    const order = r.rows[0];
    if (order.user_id !== userId && role !== "admin") throw new AppError("Not authorized", StatusCodes.FORBIDDEN);
    return order;
  }

  async updateStatus(orderId: number, status: string, existingClient?: PoolClient) {
    if (existingClient) {
      return this.updateStatusWithClient(existingClient, orderId, status);
    }

    const client = await pool.connect();
    try {
      await client.query("BEGIN");
      const order = await this.updateStatusWithClient(client, orderId, status);
      await client.query("COMMIT");
      return order;
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  private async updateStatusWithClient(client: PoolClient, orderId: number, status: string) {
    const current = await client.query("SELECT * FROM orders WHERE id=$1 FOR UPDATE", [orderId]);
    if (current.rows.length === 0) throw new AppError("Order not found", StatusCodes.NOT_FOUND);
    const currentStatus = current.rows[0].status as string;

    if (currentStatus === status) {
      return current.rows[0];
    }

    const allowedNextStatuses = ALLOWED_STATUS_TRANSITIONS[currentStatus] ?? new Set<string>();
    if (!allowedNextStatuses.has(status)) {
      throw new AppError(
        `Invalid order status transition from "${currentStatus}" to "${status}"`,
        StatusCodes.CONFLICT
      );
    }

    // If cancelling, restore stock
    if (status === "cancelled" && currentStatus !== "cancelled") {
      const items = await client.query("SELECT product_id, quantity FROM order_items WHERE order_id=$1", [orderId]);
      for (const item of items.rows) {
        await client.query("UPDATE products SET stock=stock+$1,updated_at=NOW() WHERE id=$2", [item.quantity, item.product_id]);
      }
    }

    const r = await client.query(
      "UPDATE orders SET status=$1, updated_at=NOW() WHERE id=$2 RETURNING *",
      [status, orderId]
    );
    return r.rows[0];
  }

  async deleteOrder(orderId: number) {
    await this.updateStatus(orderId, "cancelled");
  }
}

export const orderService = new OrderService();
