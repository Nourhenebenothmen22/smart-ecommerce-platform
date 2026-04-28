import { Router } from 'express';
import { orderController } from '../controllers/order.controller.js';
import { authenticate } from '../middlewares/auth.middleware.js';
import { authorize } from '../middlewares/role.middleware.js';
import { validate } from '../middlewares/validate.middleware.js';
import { createOrderSchema, orderIdSchema, orderStatusSchema } from '../validators/order.schema.js';

const router = Router();

// All order routes require authentication
router.use(authenticate);

// User routes
router.post('/', validate({ body: createOrderSchema }), orderController.createOrder);
router.get('/my', orderController.getMyOrders);

// Admin routes
router.get('/', authorize('admin'), orderController.getAllOrders);
router.patch('/:id/status', authorize('admin'), validate({ params: orderIdSchema, body: orderStatusSchema }), orderController.updateOrderStatus);
router.delete('/:id', authorize('admin'), validate({ params: orderIdSchema }), orderController.deleteOrder);

// Owner or admin (checked in service)
router.get('/:id', validate({ params: orderIdSchema }), orderController.getOrderById);

export { router as orderRouter };
