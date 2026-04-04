import { Router } from 'express';
import { validate } from '../middlewares/validate.middleware.js';
import { loginSchema, registerSchema } from '../validators/auth.schema.js';

const router = Router();

// Registration route with validation
router.post('/register', validate({ body: registerSchema }), (req, res) => {
  // Logic to register user
  res.status(201).json({ message: 'User registered successfully', data: req.body });
});

// Login route with validation
router.post('/login', validate({ body: loginSchema }), (req, res) => {
  // Logic to login user
  res.status(200).json({ message: 'Login successful', data: req.body });
});

export default router;
