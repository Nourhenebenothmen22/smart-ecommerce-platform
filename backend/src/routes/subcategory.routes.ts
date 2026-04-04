import { Router } from 'express';
import { validate } from '../middlewares/validate.middleware.js';
import { subcategorySchema, subcategoryIdSchema } from '../validators/subcategory.schema.js';
import { subcategoryController } from '../controllers/subcategory.controller.js';

const router = Router();

// TODO: Create methods in controllers and call them here
router.get('/', (req, res) => res.status(501).json({ message: 'Not implemented' }));
router.get('/:id', validate({ params: subcategoryIdSchema }), (req, res) => res.status(501).json({ message: 'Not implemented' }));
router.post('/', validate({ body: subcategorySchema }), (req, res) => res.status(501).json({ message: 'Not implemented' }));
router.patch('/:id', validate({ params: subcategoryIdSchema, body: subcategorySchema.partial() }), (req, res) => res.status(501).json({ message: 'Not implemented' }));
router.delete('/:id', validate({ params: subcategoryIdSchema }), (req, res) => res.status(501).json({ message: 'Not implemented' }));

export { router as subcategoryRouter };
