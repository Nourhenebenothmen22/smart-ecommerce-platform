import { Router } from 'express';
import { productController } from '../controllers/product.controller.js';
import { validate } from '../middlewares/validate.middleware.js';
import { productSchema, productIdSchema } from '../validators/product.schema.js';

const router = Router();

router.get('/', productController.getAllProducts);
router.get('/:id', validate({ params: productIdSchema }), productController.getProductById);
router.post('/', validate({ body: productSchema }), productController.createProduct);
router.patch('/:id', validate({ params: productIdSchema, body: productSchema.partial() }), productController.updateProduct);
router.delete('/:id', validate({ params: productIdSchema }), productController.deleteProduct);

export { router as productRouter };