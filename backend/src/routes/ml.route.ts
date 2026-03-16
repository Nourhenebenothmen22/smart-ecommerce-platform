import { Router } from "express";
import { mlController } from "../controllers/ml.controller.js";

const router = Router();

// Recalculate features (Admin only - middleware should be added here in real scenario)
router.post("/recalculate-features", (req, res) => mlController.recalculateFeatures(req, res));

// Update segments (ML pipeline endpoint)
router.post("/segments", (req, res) => mlController.updateSegments(req, res));

// Register model
router.post("/models", (req, res) => mlController.registerModel(req, res));

export const mlRouter = router;
