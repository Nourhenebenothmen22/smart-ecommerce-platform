import { Router } from 'express';
import { cartController } from '../controllers/cart.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { cartItemSchema, updateCartItemSchema, cartProductIdSchema } from '../validators/cart.schema.js';

const router = Router();

router.use(authenticate);

router.get('/', cartController.getCart);
router.post('/', validate({ body: cartItemSchema }), cartController.addItem);
router.patch('/:productId', validate({ params: cartProductIdSchema, body: updateCartItemSchema }), cartController.updateItem);
router.delete('/:productId', validate({ params: cartProductIdSchema }), cartController.removeItem);

export { router as cartRouter };
