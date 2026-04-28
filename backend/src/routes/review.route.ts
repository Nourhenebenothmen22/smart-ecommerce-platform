import { Router } from 'express';
import { reviewController } from '../controllers/review.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { reviewSchema, updateReviewSchema, reviewIdSchema, productIdSchemaLegacy } from '../validators/review.schema.js';

const router = Router();

// Public: get reviews for a product (legacy route kept for backward compat)
router.get('/product/:id', validate({ params: productIdSchemaLegacy }), reviewController.getProductReviews);

// Authenticated routes
router.post('/', authenticate, validate({ body: reviewSchema }), reviewController.addReview);
router.patch('/:id', authenticate, validate({ params: reviewIdSchema, body: updateReviewSchema }), reviewController.updateReview);
router.delete('/:id', authenticate, validate({ params: reviewIdSchema }), reviewController.deleteReview);

export { router as reviewRouter };
