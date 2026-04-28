import { Router } from 'express';
import { productController } from '../controllers/product.controller.js';
import { reviewController } from '../controllers/review.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { authorize } from '../middlewares/role.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { productSchema, productIdSchema, productQuerySchema } from '../validators/product.schema.js';
import { uploadProductImages } from '../middlewares/upload.middleware.js';

const router = Router();

// Public routes
router.get('/', validate({ query: productQuerySchema }), productController.getAllProducts);
router.get('/:id', validate({ params: productIdSchema }), productController.getProductById);
router.get('/:productId/reviews', reviewController.getProductReviews);

// Admin routes
router.post('/', authenticate, authorize('admin'), uploadProductImages.array('images', 8), validate({ body: productSchema.partial() }), productController.createProduct);
router.patch('/:id', authenticate, authorize('admin'), uploadProductImages.array('images', 8), validate({ params: productIdSchema }), productController.updateProduct);
router.delete('/:id', authenticate, authorize('admin'), validate({ params: productIdSchema }), productController.deleteProduct);

export { router as productRouter };