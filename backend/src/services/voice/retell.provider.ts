/**
 * retell.provider.ts
 * ───────────────────
 * Retell AI implementation of IVoiceProvider.
 *
 * Retell docs: https://docs.retellai.com/api-references/create-phone-call
 *
 * Required env vars:
 *   RETELL_API_KEY          – your Retell secret key
 *   RETELL_AGENT_ID         – pre-built phone agent ID from Retell dashboard
 *   RETELL_FROM_NUMBER      – caller phone number in E.164 format
 *   RETELL_WEBHOOK_SECRET   – optional HMAC secret set in Retell dashboard
 */

import crypto from "crypto";
import {
  IVoiceProvider,
  CallContext,
  DispatchResult,
  WebhookResult,
  CallOutcome,
} from "./voiceProvider.adapter.js";

export class RetellProvider implements IVoiceProvider {
  readonly name = "retell";

  private readonly apiKey: string;
  private readonly agentId: string;
  private readonly fromNumber: string;
  private readonly webhookSecret: string | undefined;
  private readonly baseUrl = "https://api.retellai.com";

  constructor() {
    this.apiKey = process.env.RETELL_API_KEY ?? "";
    this.agentId = process.env.RETELL_AGENT_ID ?? "";
    this.fromNumber = process.env.RETELL_FROM_NUMBER ?? "";
    this.webhookSecret = process.env.RETELL_WEBHOOK_SECRET;

    if (!this.apiKey || !this.agentId || !this.fromNumber) {
      throw new Error(
        "RetellProvider: RETELL_API_KEY, RETELL_AGENT_ID, and RETELL_FROM_NUMBER must be set."
      );
    }
  }

  async dispatch(ctx: CallContext): Promise<DispatchResult> {
    const body = {
      from_number: this.fromNumber,
      to_number: ctx.phone,
      agent_id: this.agentId,
      retell_llm_dynamic_variables: {
        customer_name: ctx.customerName,
        order_id: String(ctx.orderId),
        items_summary: ctx.itemsSummary,
        total_amount: ctx.totalAmount,
        delivery_address: ctx.deliveryAddress,
        payment_status: ctx.paymentStatus,
      },
      webhook_url: ctx.webhookUrl,
    };

    const response = await fetch(`${this.baseUrl}/v2/create-phone-call`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Retell dispatch failed [${response.status}]: ${err}`);
    }

    const data = (await response.json()) as { call_id: string };
    return { providerCallId: data.call_id };
  }

  parseWebhook(body: unknown, rawBody: Buffer, signature: string): WebhookResult | null {
    // Validate HMAC signature if secret is configured
    if (this.webhookSecret) {
      const expected = crypto
        .createHmac("sha256", this.webhookSecret)
        .update(rawBody)
        .digest("hex");
      const trusted = `sha256=${expected}`;
      if (!crypto.timingSafeEqual(Buffer.from(trusted), Buffer.from(signature))) {
        return null; // signature mismatch → reject
      }
    }

    const payload = body as Record<string, unknown>;
    const callId = payload["call_id"] as string | undefined;
    if (!callId) return null;

    const event = payload["event"] as string | undefined;
    const transcript = payload["transcript"] as string | undefined;

    // Map Retell events → our normalised outcome
    let outcome: CallOutcome = "unclear";

    if (event === "call_ended") {
      const disconnectionReason = payload["disconnection_reason"] as string | undefined;
      const callAnalysis = payload["call_analysis"] as Record<string, unknown> | undefined;

      // call_analysis.call_successful is set by the Retell agent when it
      // explicitly captures a "yes/confirm" or "no/cancel" response.
      const successful = callAnalysis?.["call_successful"] as boolean | undefined;
      const userConfirmed = callAnalysis?.["custom_analysis_data"] as
        | { confirmed?: boolean; cancelled?: boolean }
        | undefined;

      if (disconnectionReason === "no_answer" || disconnectionReason === "voicemail") {
        outcome = "no_answer";
      } else if (userConfirmed?.confirmed === true || successful === true) {
        outcome = "confirmed";
      } else if (userConfirmed?.cancelled === true) {
        outcome = "cancelled";
      } else {
        outcome = "unclear";
      }
    } else {
      // Non-terminal events (call_started, etc.) – ignore
      return null;
    }

    return { providerCallId: callId, outcome, transcript };
  }
}
