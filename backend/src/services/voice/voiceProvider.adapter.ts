/**
 * voiceProvider.adapter.ts
 * ─────────────────────────
 * Provider-agnostic interface for outbound voice calls.
 * Add a new provider by implementing IVoiceProvider and
 * registering it in phoneConfirmation.service.ts.
 */

export interface CallContext {
  orderId: number;
  customerName: string;
  phone: string;
  /** Summary of ordered items, e.g. "2x Laptop, 1x Mouse" */
  itemsSummary: string;
  /** Formatted total, e.g. "$349.00" */
  totalAmount: string;
  /** Full delivery address assembled from user record */
  deliveryAddress: string;
  /** Safe payment descriptor, e.g. "Paid via credit card" – no card numbers */
  paymentStatus: string;
  /** Public base URL the provider will POST results back to */
  webhookUrl: string;
}

export interface DispatchResult {
  /** Provider-assigned call identifier for deduplication / webhook matching */
  providerCallId: string;
}

export interface IVoiceProvider {
  readonly name: string;
  /**
   * Initiate an outbound call.
   * Must return the provider call-id immediately (call is async).
   */
  dispatch(ctx: CallContext): Promise<DispatchResult>;

  /**
   * Parse the incoming webhook payload into a normalised result.
   * Returns null if the payload does not belong to this provider.
   */
  parseWebhook(body: unknown, rawBody: Buffer, signature: string): WebhookResult | null;
}

export type CallOutcome =
  | "confirmed"
  | "cancelled"
  | "no_answer"
  | "unclear";

export interface WebhookResult {
  providerCallId: string;
  outcome: CallOutcome;
  /** Raw transcript from the call, if available */
  transcript?: string;
}
