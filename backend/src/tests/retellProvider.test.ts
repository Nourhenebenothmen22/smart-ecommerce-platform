import crypto from "crypto";
import { env } from "../config/env.js";
import { RetellProvider } from "../services/voice/retell.provider.js";

describe("RetellProvider webhook verification", () => {
  beforeEach(() => {
    (env as any).RETELL_API_KEY = "test-api-key";
    (env as any).RETELL_AGENT_ID = "agent-123";
    (env as any).RETELL_FROM_NUMBER = "+15551234567";
    (env as any).RETELL_WEBHOOK_SECRET = "webhook-secret";
  });

  test("requires webhook secret configuration", () => {
    (env as any).RETELL_WEBHOOK_SECRET = "";

    expect(() => new RetellProvider()).toThrow("RETELL_WEBHOOK_SECRET");
  });

  test("rejects malformed signatures without throwing", () => {
    const provider = new RetellProvider();

    expect(
      provider.parseWebhook({ call_id: "call_1", event: "call_ended" }, Buffer.from("{}"), "bad")
    ).toBeNull();
  });

  test("accepts valid signatures", () => {
    const provider = new RetellProvider();
    const body = {
      call_id: "call_1",
      event: "call_ended",
      call_analysis: {
        custom_analysis_data: { confirmed: true },
      },
    };
    const rawBody = Buffer.from(JSON.stringify(body));
    const signature = `sha256=${crypto
      .createHmac("sha256", "webhook-secret")
      .update(rawBody)
      .digest("hex")}`;

    expect(provider.parseWebhook(body, rawBody, signature)).toEqual({
      providerCallId: "call_1",
      outcome: "confirmed",
      transcript: undefined,
    });
  });
});
