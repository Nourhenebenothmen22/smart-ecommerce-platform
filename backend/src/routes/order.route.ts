import { Router } from 'express';
import { orderController } from '../controllers/order.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { orderSchema, orderIdSchema, orderStatusSchema } from '../validators/order.schema.js';

const router = Router();

router.use(authenticate);

router.post('/', validate({ body: orderSchema }), orderController.createOrder);
router.get('/my-orders', orderController.getMyOrders);
router.get('/:id', validate({ params: orderIdSchema }), orderController.getOrderById);
router.patch('/:id/status', validate({ params: orderIdSchema, body: orderStatusSchema }), orderController.updateOrderStatus);

export { router as orderRouter };
