import { Router } from "express";
import { mlController } from "../controllers/ml.controller.js";
import { authenticate } from "../middlewares/auth.middleware.js";
import { authorize } from "../middlewares/role.middleware.js";

const router = Router();

// All ML routes require admin authentication
router.use(authenticate);
router.use(authorize("admin"));

router.post("/recalculate-features", (req, res, next) => mlController.recalculateFeatures(req, res, next));
router.post("/segments", (req, res, next) => mlController.updateSegments(req, res, next));
router.post("/models", (req, res, next) => mlController.registerModel(req, res, next));
router.post("/price/predict", (req, res, next) => mlController.predictProductPrice(req, res, next));

export const mlRouter = router;
