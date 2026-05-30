import { Router } from "express";
import { mlController } from "../controllers/ml.controller.js";
import { authenticate } from "../middlewares/auth.middleware.js";
import { authorize } from "../middlewares/role.middleware.js";

const router = Router();

// All ML routes require admin authentication
router.use(authenticate);
router.use(authorize("admin"));

router.post("/recalculate-features", mlController.recalculateFeatures);
router.post("/segments", mlController.updateSegments);
router.post("/models", mlController.registerModel);
router.post("/price/predict", mlController.predictProductPrice);

export const mlRouter = router;
