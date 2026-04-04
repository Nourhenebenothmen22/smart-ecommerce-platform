import { Request, Response } from "express";
import { z } from "zod";
import { mlService } from "../services/ml.service.js";

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
  async recalculateFeatures(_req: Request, res: Response) {
    try {
      await mlService.recalculateUserFeatures();
      res.status(200).json({
        success: true,
        message: "Recalculation of user features started/completed successfully."
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred";
      res.status(500).json({
        success: false,
        message: "Failed to recalculate features",
        error: errorMessage
      });
    }
  }

  /**
   * Endpoint for ML pipeline to push batch segmentation results.
   * POST /api/ml/segments
   */
  async updateSegments(req: Request, res: Response) {
    const parsed = segmentsBodySchema.safeParse(req.body);

    if (!parsed.success) {
      res.status(400).json({
        success: false,
        message: "Validation failed",
        errors: parsed.error.flatten().fieldErrors,
      });
      return;
    }

    try {
      await mlService.recordUserSegments(parsed.data.segments);
      res.status(200).json({
        success: true,
        message: `Successfully updated ${parsed.data.segments.length} user segments.`
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred";
      res.status(500).json({
        success: false,
        message: "Failed to update segments",
        error: errorMessage
      });
    }
  }

  /**
   * Registers a model version after training.
   * POST /api/ml/models
   */
  async registerModel(req: Request, res: Response) {
    const parsed = registerModelSchema.safeParse(req.body);

    if (!parsed.success) {
      res.status(400).json({
        success: false,
        message: "Validation failed",
        errors: parsed.error.flatten().fieldErrors,
      });
      return;
    }

    try {
      await mlService.registerModel(parsed.data);
      res.status(201).json({
        success: true,
        message: "Model registered successfully."
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred";
      res.status(500).json({
        success: false,
        message: "Failed to register model",
        error: errorMessage
      });
    }
  }
}

export const mlController = new MLController();
