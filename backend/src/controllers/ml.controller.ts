import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { z } from "zod";
import { mlService } from "../services/ml.service.js";
import { sendResponse } from "../utils/apiResponse.js";

// ─── Zod Schemas ────────────────────────────────────────────

const segmentSchema = z.object({
  user_id: z.number().int().positive(),
  segment_id: z.number().int().min(0),
  segment_label: z.string().min(1).max(100),
  model_name: z.string().min(1).max(120),
  model_version: z.string().min(1).max(50),
  confidence: z.number().min(0).max(1).optional(),
});

const segmentsBodySchema = z.object({
  segments: z.array(segmentSchema).min(1),
});

const registerModelSchema = z.object({
  model_name: z.string().min(1).max(120),
  model_version: z.string().min(1).max(50),
  model_type: z.string().min(1).max(50),
  algorithm: z.string().min(1).max(50),
  metrics: z.record(z.string(), z.unknown()).optional(),
  parameters: z.record(z.string(), z.unknown()).optional(),
  artifact_path: z.string().max(500).optional(),
});

// ─── Controller ─────────────────────────────────────────────

export class MLController {
  /**
   * Triggers a manual recalculation of all user features.
   * POST /api/ml/recalculate-features
   */
  async recalculateFeatures(_req: Request, res: Response, next: NextFunction) {
    try {
      await mlService.recalculateUserFeatures();
      sendResponse(res, StatusCodes.OK, "Recalculation of user features started/completed successfully.");
    } catch (error: unknown) {
      next(error);
    }
  }

  /**
   * Endpoint for ML pipeline to push batch segmentation results.
   * POST /api/ml/segments
   */
  async updateSegments(req: Request, res: Response, next: NextFunction) {
    const parsed = segmentsBodySchema.safeParse(req.body);

    if (!parsed.success) {
      return sendResponse(res, StatusCodes.BAD_REQUEST, "Validation failed", null, parsed.error.flatten().fieldErrors);
    }

    try {
      await mlService.recordUserSegments(parsed.data.segments);
      sendResponse(res, StatusCodes.OK, `Successfully updated ${parsed.data.segments.length} user segments.`);
    } catch (error: unknown) {
      next(error);
    }
  }

  /**
   * Registers a model version after training.
   * POST /api/ml/models
   */
  async registerModel(req: Request, res: Response, next: NextFunction) {
    const parsed = registerModelSchema.safeParse(req.body);

    if (!parsed.success) {
      return sendResponse(res, StatusCodes.BAD_REQUEST, "Validation failed", null, parsed.error.flatten().fieldErrors);
    }

    try {
      await mlService.registerModel(parsed.data);
      sendResponse(res, StatusCodes.CREATED, "Model registered successfully.");
    } catch (error: unknown) {
      next(error);
    }
  }
}

export const mlController = new MLController();
