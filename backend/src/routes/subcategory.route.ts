import { Router } from 'express';
import { subcategoryController } from '../controllers/subcategory.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { authorize } from '../middlewares/role.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { subcategorySchema, subcategoryIdSchema } from '../validators/subcategory.schema.js';

const router = Router();

// Public routes
router.get('/', subcategoryController.getAllSubcategories);
router.get('/:id', validate({ params: subcategoryIdSchema }), subcategoryController.getSubcategoryById);

// Admin routes
router.post('/', authenticate, authorize('admin'), validate({ body: subcategorySchema }), subcategoryController.createSubcategory);
router.patch('/:id', authenticate, authorize('admin'), validate({ params: subcategoryIdSchema, body: subcategorySchema.partial() }), subcategoryController.updateSubcategory);
router.delete('/:id', authenticate, authorize('admin'), validate({ params: subcategoryIdSchema }), subcategoryController.deleteSubcategory);

export { router as subcategoryRouter };
