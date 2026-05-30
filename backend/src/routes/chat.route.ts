import { Router } from "express";
import { chatController } from "../controllers/chat.controller.js";
import { authenticate } from "../middlewares/auth.middleware.js";
import { authorize } from "../middlewares/role.middleware.js";

const router = Router();

router.post("/", authenticate, authorize("customer"), chatController.sendMessage);

export { router as chatRouter };
