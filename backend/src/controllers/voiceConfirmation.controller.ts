/**
 * voiceConfirmation.controller.ts
 * ────────────────────────────────
 * Controller for:
 *  - POST /api/voice/webhook       → provider calls this when call ends
 *  - POST /api/voice/initiate/:id  → admin triggers a confirmation call
 *  - GET  /api/voice/context/:id   → admin fetches confirmation history
 */

import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { sendResponse } from "../utils/apiResponse.js";
import { PhoneConfirmationService } from "../services/phoneConfirmation.service.js";
import { RetellProvider } from "../services/voice/retell.provider.js";
import { env } from "../config/env.js";
import { AppError } from "../utils/AppError.js";

// ── Lazy singleton ──────────────────────────────────────────────────────────
let _service: PhoneConfirmationService | null = null;

function getService(): PhoneConfirmationService {
  if (!_service) {
    // Switch provider here when needed (e.g. new TwilioProvider())
    const provider = new RetellProvider();
    _service = new PhoneConfirmationService(provider);
  }
  return _service;
}

export class VoiceConfirmationController {
  /**
   * POST /api/voice/webhook
   * Called by the voice provider when a call completes.
   * No authentication — validated via HMAC signature instead.
   */
  async webhook(req: Request, res: Response, next: NextFunction) {
    try {
      const service = getService();

      if (!Buffer.isBuffer(req.body)) {
        throw new AppError("Webhook raw body is required", StatusCodes.BAD_REQUEST);
      }

      const rawBody = req.body;
      const signature = (req.headers["x-retell-signature"] as string) ?? "";

      const result = await service.handleWebhookResult(rawBody, signature);

      if (!result) {
        return sendResponse(res, StatusCodes.OK, "Ignored (unknown or invalid payload)");
      }

      sendResponse(res, StatusCodes.OK, `Order ${result.orderId}: ${result.outcome}`);
    } catch (error) {
      next(error);
    }
  }

  /**
   * POST /api/voice/initiate/:id
   * Manually trigger a phone confirmation call for an order. Admin only.
   */
  async initiateCall(req: Request, res: Response, next: NextFunction) {
    try {
      const service = getService();
      const orderId = Number(req.params.id);
      const webhookBaseUrl = env.WEBHOOK_BASE_URL || `${req.protocol}://${req.get("host")}`;

      const result = await service.initiateCall(orderId, webhookBaseUrl);

      sendResponse(res, StatusCodes.OK, "Confirmation call initiated", {
        orderId,
        providerCallId: result.providerCallId,
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/voice/context/:id
   * Retrieve the confirmation call history for an order. Admin only.
   */
  async getContext(req: Request, res: Response, next: NextFunction) {
    try {
      const service = getService();
      const orderId = Number(req.params.id);
      const context = await service.getConfirmationContext(orderId);

      sendResponse(res, StatusCodes.OK, "Confirmation context retrieved", context);
    } catch (error) {
      next(error);
    }
  }
}

export const voiceConfirmationController = new VoiceConfirmationController();
