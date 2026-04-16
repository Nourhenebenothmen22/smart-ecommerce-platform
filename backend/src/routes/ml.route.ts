import { Router } from "express";
import { mlController } from "../controllers/ml.controller.js";
import { authenticate } from "../middlewares/auth.middleware.js";

const router = Router();

// Apply authentication to all ML routes
router.use(authenticate);

// Recalculate features (Admin only - ideally we check for admin role here too)
router.post("/recalculate-features", (req, res, next) => mlController.recalculateFeatures(req, res, next));

// Update segments (ML pipeline endpoint)
router.post("/segments", (req, res, next) => mlController.updateSegments(req, res, next));

// Register model
router.post("/models", (req, res, next) => mlController.registerModel(req, res, next));

export const mlRouter = router;
