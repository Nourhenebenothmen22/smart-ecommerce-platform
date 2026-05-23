/**
 * phoneConfirmation.service.ts
 * ─────────────────────────────
 * Core business logic for phone-based order confirmation.
 *
 * Responsibilities:
 *  - Build the call context from order + user data
 *  - Prevent duplicate active calls (DB unique index + app-level check)
 *  - Dispatch call via the pluggable voice provider
 *  - Process webhook results → update order status
 *  - Retry logic for no-answer calls
 */

import { pool } from "../db/pool.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";
import { orderService } from "./order.service.js";
import { env } from "../config/env.js";
import type {
  IVoiceProvider,
  CallContext,
  CallOutcome,
  WebhookResult,
} from "./voice/voiceProvider.adapter.js";

// ─── Constants ───────────────────────────────────────────────────────────────
const MAX_RETRIES = 3;
const PHONE_E164_REGEX = /^\+[1-9]\d{6,14}$/;

// ─── Service ─────────────────────────────────────────────────────────────────
export class PhoneConfirmationService {
  private provider: IVoiceProvider;

  constructor(provider: IVoiceProvider) {
    this.provider = provider;
  }

  // ── 1. Initiate a confirmation call ────────────────────────────────────────
  async initiateCall(orderId: number, webhookBaseUrl: string): Promise<{ providerCallId: string }> {
    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      // 1a. Load order + items
      const orderRes = await client.query(
        `SELECT o.id, o.user_id, o.total_amount, o.status, o.payment_status
         FROM orders o WHERE o.id = $1 FOR UPDATE`,
        [orderId]
      );
      if (orderRes.rows.length === 0) {
        throw new AppError("Order not found", StatusCodes.NOT_FOUND);
      }
      const order = orderRes.rows[0];

      if (order.status !== "pending_phone_confirmation") {
        throw new AppError(
          `Order ${orderId} is in status "${order.status}" — cannot initiate confirmation call.`,
          StatusCodes.CONFLICT
        );
      }

      // 1b. Duplicate-call prevention (app-level, backed by DB unique index)
      const activeCall = await client.query(
        `SELECT id FROM voice_confirmations
         WHERE order_id = $1 AND call_status NOT IN ('completed','failed','cancelled')
         LIMIT 1`,
        [orderId]
      );
      if (activeCall.rows.length > 0) {
        throw new AppError(
          `A call for order ${orderId} is already in progress.`,
          StatusCodes.CONFLICT
        );
      }

      // 1c. Load user
      const userRes = await client.query(
        `SELECT id, first_name, last_name, phone, address_line, city, postal_code, country
         FROM users WHERE id = $1`,
        [order.user_id]
      );
      if (userRes.rows.length === 0) {
        throw new AppError("User not found", StatusCodes.NOT_FOUND);
      }
      const user = userRes.rows[0];

      // 1d. Validate phone
      const phone: string | null = user.phone;
      if (!phone || !PHONE_E164_REGEX.test(phone)) {
        throw new AppError(
          "User has no valid phone number on file. Phone confirmation cannot proceed.",
          StatusCodes.UNPROCESSABLE_ENTITY
        );
      }

      // 1e. Load order items
      const itemsRes = await client.query(
        `SELECT product_name_snapshot, quantity, unit_price FROM order_items WHERE order_id = $1`,
        [orderId]
      );
      const itemsSummary = itemsRes.rows
        .map((r: any) => `${r.quantity}× ${r.product_name_snapshot}`)
        .join(", ");

      // 1f. Build safe payment descriptor (never expose card details)
      const paymentRes = await client.query(
        `SELECT payment_method, status FROM payments WHERE order_id = $1 LIMIT 1`,
        [orderId]
      );
      const paymentInfo = paymentRes.rows[0];
      const paymentStatus = paymentInfo
        ? `${paymentInfo.status} via ${paymentInfo.payment_method}`
        : "pending";

      // 1g. Assemble delivery address
      const addressParts = [user.address_line, user.city, user.postal_code, user.country]
        .filter(Boolean);
      const deliveryAddress = addressParts.length > 0 ? addressParts.join(", ") : "Not provided";

      // 1h. Build call context
      const ctx: CallContext = {
        orderId,
        customerName: `${user.first_name} ${user.last_name}`,
        phone,
        itemsSummary: itemsSummary || "No items",
        totalAmount: `$${parseFloat(order.total_amount).toFixed(2)}`,
        deliveryAddress,
        paymentStatus,
        webhookUrl: `${webhookBaseUrl}/api/voice/webhook`,
      };

      // 1i. Dispatch via provider
      const result = await this.provider.dispatch(ctx);

      // 1j. Persist voice_confirmation record
      await client.query(
        `INSERT INTO voice_confirmations
           (order_id, phone_number, call_status, provider_call_id, retry_count)
         VALUES ($1, $2, 'in_progress', $3, 0)`,
        [orderId, phone, result.providerCallId]
      );

      await client.query("COMMIT");
      return { providerCallId: result.providerCallId };
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  // ── 2. Handle webhook result ───────────────────────────────────────────────
  async handleWebhookResult(
    rawBody: Buffer,
    signature: string
  ): Promise<{ orderId: number; outcome: CallOutcome } | null> {
    const parsed = this.provider.parseWebhook(rawBody, signature);
    if (!parsed) return null;

    const { providerCallId, outcome, transcript } = parsed;

    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      // Find the confirmation record
      const vcRes = await client.query(
        `SELECT vc.id, vc.order_id, vc.retry_count
         FROM voice_confirmations vc
         WHERE vc.provider_call_id = $1
         FOR UPDATE`,
        [providerCallId]
      );
      if (vcRes.rows.length === 0) {
        await client.query("ROLLBACK");
        return null;
      }

      const vc = vcRes.rows[0];
      const orderId: number = vc.order_id;

      // Map outcome → order status + voice_confirmations update
      let newOrderStatus: string;
      let newCallStatus: string;
      let confirmed: boolean;

      switch (outcome) {
        case "confirmed":
          newOrderStatus = "processing";
          newCallStatus = "completed";
          confirmed = true;
          break;
        case "cancelled":
          newOrderStatus = "cancelled";
          newCallStatus = "completed";
          confirmed = false;
          break;
        case "no_answer":
          // Keep order as pending, mark call as failed, potentially retry
          newOrderStatus = "pending_phone_confirmation";
          newCallStatus = "failed";
          confirmed = false;
          break;
        case "unclear":
          newOrderStatus = "manual_review";
          newCallStatus = "completed";
          confirmed = false;
          break;
        default:
          newOrderStatus = "manual_review";
          newCallStatus = "completed";
          confirmed = false;
      }

      // Update voice_confirmations
      await client.query(
        `UPDATE voice_confirmations
         SET call_status = $1,
             transcript  = $2,
             confirmed   = $3,
             confirmed_at = CASE WHEN $3 THEN NOW() ELSE confirmed_at END,
             retry_count  = CASE WHEN $4 = 'no_answer' THEN retry_count + 1 ELSE retry_count END
         WHERE id = $5`,
        [newCallStatus, transcript ?? null, confirmed, outcome, vc.id]
      );

      // Update order status (reuse existing updateStatus which handles stock restoration on cancel)
      if (outcome !== "no_answer") {
        await orderService.updateStatus(orderId, newOrderStatus, client);
      }
      // If no_answer → order stays pending, we schedule a retry in the background

      await client.query("COMMIT");

      // After commit: schedule retry if applicable
      if (outcome === "no_answer" && vc.retry_count < MAX_RETRIES) {
        this.scheduleRetry(orderId, vc.retry_count + 1);
      }

      return { orderId, outcome };
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  // ── 3. Retry logic ────────────────────────────────────────────────────────
  private scheduleRetry(orderId: number, currentRetryCount: number): void {
    const delayMs = Math.min(currentRetryCount * 60_000, 5 * 60_000); // 1m, 2m, 3m (capped at 5m)
    console.log(
      `[PhoneConfirmation] Scheduling retry #${currentRetryCount} for order ${orderId} in ${delayMs / 1000}s`
    );
    setTimeout(async () => {
      try {
        const webhookBaseUrl = env.WEBHOOK_BASE_URL || "https://localhost:5000";
        await this.initiateCall(orderId, webhookBaseUrl);
      } catch (err) {
        console.error(`[PhoneConfirmation] Retry #${currentRetryCount} failed for order ${orderId}:`, err);
      }
    }, delayMs);
  }

  // ── 4. Get confirmation context for an order (admin API) ──────────────────
  async getConfirmationContext(orderId: number) {
    const res = await pool.query(
      `SELECT vc.*, o.status AS order_status, o.total_amount,
              u.first_name, u.last_name, u.phone
       FROM voice_confirmations vc
       JOIN orders o ON o.id = vc.order_id
       JOIN users u ON u.id = o.user_id
       WHERE vc.order_id = $1
       ORDER BY vc.created_at DESC`,
      [orderId]
    );
    return res.rows;
  }
}
