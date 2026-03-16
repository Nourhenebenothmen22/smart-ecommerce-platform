import { Request, Response } from "express";
import { mlService } from "../services/ml.service.js";

export class MLController {
  /**
   * Triggers a manual recalculation of all user features.
   * POST /api/admin/ml/recalculate-features
   */
  async recalculateFeatures(req: Request, res: Response) {
    try {
      await mlService.recalculateUserFeatures();
      res.status(200).json({
        success: true,
        message: "Recalculation of user features started/completed successfully."
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        message: "Failed to recalculate features",
        error: error.message
      });
    }
  }

  /**
   * Endpoint for ML pipeline to push batch segmentation results.
   * POST /api/admin/ml/segments
   */
  async updateSegments(req: Request, res: Response) {
    const { segments } = req.body;

    if (!Array.isArray(segments)) {
       res.status(400).json({ success: false, message: "Segments must be an array" });
       return;
    }

    try {
      await mlService.recordUserSegments(segments);
      res.status(200).json({
        success: true,
        message: `Successfully updated ${segments.length} user segments.`
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        message: "Failed to update segments",
        error: error.message
      });
    }
  }

  /**
   * Registers a model version after training.
   * POST /api/admin/ml/models
   */
  async registerModel(req: Request, res: Response) {
    try {
      await mlService.registerModel(req.body);
      res.status(201).json({
        success: true,
        message: "Model registered successfully."
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        message: "Failed to register model",
        error: error.message
      });
    }
  }
}

export const mlController = new MLController();
