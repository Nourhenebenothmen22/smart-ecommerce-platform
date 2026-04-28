import { Router } from 'express';
import { categoryController } from '../controllers/category.controller.js';
import { subcategoryController } from '../controllers/subcategory.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { authorize } from '../middlewares/role.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { categorySchema, categoryIdSchema, categoryIdParamSchema } from '../validators/category.schema.js';

const router = Router();

// Public routes
router.get('/', categoryController.getAllCategories);
router.get('/:id', validate({ params: categoryIdSchema }), categoryController.getCategoryById);
router.get('/:categoryId/subcategories', validate({ params: categoryIdParamSchema }), subcategoryController.getByCategoryId);

// Admin routes
router.post('/', authenticate, authorize('admin'), validate({ body: categorySchema }), categoryController.createCategory);
router.patch('/:id', authenticate, authorize('admin'), validate({ params: categoryIdSchema, body: categorySchema.partial() }), categoryController.updateCategory);
router.delete('/:id', authenticate, authorize('admin'), validate({ params: categoryIdSchema }), categoryController.deleteCategory);

export { router as categoryRouter };
