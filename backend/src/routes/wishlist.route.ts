import { Router } from 'express';
import { wishlistController } from '../controllers/wishlist.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { wishlistItemSchema, wishlistProductIdSchema } from '../validators/wishlist.schema.js';

const router = Router();

router.use(authenticate);

router.get('/', wishlistController.getWishlist);
router.post('/', validate({ body: wishlistItemSchema }), wishlistController.addItem);
router.delete('/:productId', validate({ params: wishlistProductIdSchema }), wishlistController.removeItem);

export { router as wishlistRouter };
