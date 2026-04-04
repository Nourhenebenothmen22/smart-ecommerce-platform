import { Router } from 'express';
import { subcategoryController } from '../controllers/subcategory.controller.js';
import { validate } from '../middlewares/validate.middleware.js';
import { subcategorySchema, subcategoryIdSchema } from '../validators/subcategory.schema.js';

const router = Router();

router.get('/', subcategoryController.getAllSubcategories);
router.get('/:id', validate({ params: subcategoryIdSchema }), subcategoryController.getSubcategoryById);
router.post('/', validate({ body: subcategorySchema }), subcategoryController.createSubcategory);
router.patch('/:id', validate({ params: subcategoryIdSchema, body: subcategorySchema.partial() }), subcategoryController.updateSubcategory);
router.delete('/:id', validate({ params: subcategoryIdSchema }), subcategoryController.deleteSubcategory);

export { router as subcategoryRouter };
