/**
 * voice.route.ts
 * ──────────────
 * Routes for the phone confirmation subsystem.
 *
 * POST /api/voice/webhook        → public (signature-validated by provider)
 * POST /api/voice/initiate/:id   → admin only
 * GET  /api/voice/context/:id    → admin only
 */

import { Router, raw } from "express";
import { voiceConfirmationController } from "../controllers/voiceConfirmation.controller.js";
import { authenticate } from "../middlewares/auth.middleware.js";
import { authorize } from "../middlewares/role.middleware.js";
import { validate } from "../middlewares/validate.middleware.js";
import { orderIdSchema } from "../validators/order.schema.js";

const router = Router();
const webhookRouter = Router();

// ── Webhook (unauthenticated — validated via HMAC) ──────────────────────────
// The webhook needs the exact raw JSON bytes for signature verification.
webhookRouter.post(
  "/",
  raw({ type: "application/json", limit: "1mb" }),
  voiceConfirmationController.webhook
);

// ── Admin routes ────────────────────────────────────────────────────────────
router.post(
  "/initiate/:id",
  authenticate,
  authorize("admin"),
  validate({ params: orderIdSchema }),
  voiceConfirmationController.initiateCall
);

router.get(
  "/context/:id",
  authenticate,
  authorize("admin"),
  validate({ params: orderIdSchema }),
  voiceConfirmationController.getContext
);

export { router as voiceRouter, webhookRouter as voiceWebhookRouter };
