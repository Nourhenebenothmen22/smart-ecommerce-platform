import { Router } from 'express';
import { userController } from '../controllers/user.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { authorize } from '../middlewares/role.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { userIdSchema, updateProfileSchema, updateRoleSchema, updateStatusSchema } from '../validators/user.schema.js';

const router = Router();

// All user routes require authentication
router.use(authenticate);

// Current user routes
router.get('/me', userController.getMe);
router.patch('/me', validate({ body: updateProfileSchema }), userController.updateMe);

// Admin routes
router.get('/', authorize('admin'), userController.getAllUsers);
router.get('/:id', authorize('admin'), validate({ params: userIdSchema }), userController.getUserById);
router.patch('/:id/role', authorize('admin'), validate({ params: userIdSchema, body: updateRoleSchema }), userController.updateRole);
router.patch('/:id/status', authorize('admin'), validate({ params: userIdSchema, body: updateStatusSchema }), userController.updateStatus);
router.delete('/:id', authorize('admin'), validate({ params: userIdSchema }), userController.deleteUser);

export { router as userRouter };
