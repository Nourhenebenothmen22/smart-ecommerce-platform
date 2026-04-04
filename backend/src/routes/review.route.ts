import { Router } from 'express';
import { reviewController } from '../controllers/review.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { reviewSchema, reviewIdSchema, productIdSchema } from '../validators/review.schema.js';

const router = Router();

router.get('/product/:id', validate({ params: productIdSchema }), reviewController.getProductReviews);

router.use(authenticate);

router.post('/', validate({ body: reviewSchema }), reviewController.createReview);
router.delete('/:id', validate({ params: reviewIdSchema }), reviewController.deleteReview);

export { router as reviewRouter };
