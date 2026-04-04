import express from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import dotenv from "dotenv";
import debug from "debug";

import type { ErrorRequestHandler } from "express";

import { healthRouter } from "./routes/health.route.js";
import { mlRouter } from "./routes/ml.route.js";
import { authRouter } from "./routes/auth.routes.js";
import { userRouter } from "./routes/user.routes.js";
import { productRouter } from "./routes/product.routes.js";
import { categoryRouter } from "./routes/category.routes.js";
import { subcategoryRouter } from "./routes/subcategory.routes.js";
import { orderRouter } from "./routes/order.routes.js";
import { reviewRouter } from "./routes/review.routes.js";

dotenv.config();

const log = debug("app:server");

export const app = express();

/*
Security Middleware
*/
app.use(helmet());

/*
CORS
*/
app.use(cors());

/*
Body Parser
*/
app.use(express.json());

/*
HTTP Logger
*/
app.use(morgan("dev"));

/*
Rate Limiter (applied only to non-health routes)
*/
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: "Too many requests from this IP",
});

/*
Routes
*/
app.use("/api/health", healthRouter);

// Apply rate limiter to all routes except health
app.use(limiter);

app.use("/api/ml", mlRouter);
app.use("/api/auth", authRouter);
app.use("/api/users", userRouter);
app.use("/api/products", productRouter);
app.use("/api/categories", categoryRouter);
app.use("/api/subcategories", subcategoryRouter);
app.use("/api/orders", orderRouter);
app.use("/api/reviews", reviewRouter);

/*
404 Handler
*/
app.use((_req, res) => {
  res.status(404).json({
    success: false,
    message: "Route not found",
  });
});

/*
Global Error Handler (Express 5 compatible)
*/
const errorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
  log(err);

  res.status(500).json({
    success: false,
    message: "Internal Server Error",
  });
};

app.use(errorHandler);