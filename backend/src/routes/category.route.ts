import { Router } from 'express';
import { categoryController } from '../controllers/category.controller.js';
import { validate } from '../middlewares/validate.middleware.js';
import { categorySchema, categoryIdSchema } from '../validators/category.schema.js';

const router = Router();

router.get('/', categoryController.getAllCategories);
router.get('/:id', validate({ params: categoryIdSchema }), categoryController.getCategoryById);
router.post('/', validate({ body: categorySchema }), categoryController.createCategory);
router.patch('/:id', validate({ params: categoryIdSchema, body: categorySchema.partial() }), categoryController.updateCategory);
router.delete('/:id', validate({ params: categoryIdSchema }), categoryController.deleteCategory);

export { router as categoryRouter };
