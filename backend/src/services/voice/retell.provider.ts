import crypto from "crypto";
import {
  IVoiceProvider,
  CallContext,
  DispatchResult,
  WebhookResult,
  CallOutcome,
} from "./voiceProvider.adapter.js";
import { env } from "../../config/env.js";

export class RetellProvider implements IVoiceProvider {
  readonly name = "retell";

  private readonly apiKey: string;
  private readonly agentId: string;
  private readonly fromNumber: string;
  private readonly webhookSecret: string;
  private readonly baseUrl = "https://api.retellai.com";

  constructor() {
    this.apiKey = env.RETELL_API_KEY ?? "";
    this.agentId = env.RETELL_AGENT_ID ?? "";
    this.fromNumber = env.RETELL_FROM_NUMBER ?? "";
    this.webhookSecret = env.RETELL_WEBHOOK_SECRET ?? "";

    if (!this.apiKey || !this.agentId || !this.fromNumber || !this.webhookSecret) {
      throw new Error(
        "RetellProvider: RETELL_API_KEY, RETELL_AGENT_ID, RETELL_FROM_NUMBER, and RETELL_WEBHOOK_SECRET must be set."
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

  parseWebhook(rawBody: Buffer, signature: string): WebhookResult | null {
    const expected = crypto
      .createHmac("sha256", this.webhookSecret)
      .update(rawBody)
      .digest("hex");
    const trusted = `sha256=${expected}`;
    const trustedBuffer = Buffer.from(trusted);
    const signatureBuffer = Buffer.from(signature);

    if (
      signatureBuffer.length !== trustedBuffer.length ||
      !crypto.timingSafeEqual(trustedBuffer, signatureBuffer)
    ) {
      return null;
    }

    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(rawBody.toString("utf-8")) as Record<string, unknown>;
    } catch {
      return null;
    }

    const callId = payload["call_id"] as string | undefined;
    if (!callId) return null;

    const event = payload["event"] as string | undefined;
    const transcript = payload["transcript"] as string | undefined;
    let outcome: CallOutcome = "unclear";

    if (event === "call_ended") {
      const disconnectionReason = payload["disconnection_reason"] as string | undefined;
      const callAnalysis = payload["call_analysis"] as Record<string, unknown> | undefined;
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
      return null;
    }

    return { providerCallId: callId, outcome, transcript };
  }
}
