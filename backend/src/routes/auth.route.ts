import { Router } from 'express';
import { authController } from '../controllers/auth.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { authorize } from '../middlewares/role.middleware.js';
import { authRateLimitMiddleware } from '../middlewares/rateLimit.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { registerSchema, loginSchema } from '../validators/auth.schema.js';

const router = Router();

router.post('/register', authRateLimitMiddleware, validate({ body: registerSchema }), authController.register);
router.post('/register-admin', authenticate, authorize('admin'), validate({ body: registerSchema }), authController.registerAdmin);
router.post('/login', authRateLimitMiddleware, validate({ body: loginSchema }), authController.login);
router.post('/logout', authenticate, authController.logout);

export { router as authRouter };
