import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import compression from "compression";
import cookieParser from "cookie-parser";
import lusca from "lusca";
import { corsMiddleware } from "./middlewares/cors.middleware.js";
import { rateLimitMiddleware } from "./middlewares/rateLimit.middleware.js";
import { errorHandler } from "./middlewares/error.middleware.js";
import { healthRouter } from "./routes/health.route.js";
import { mlRouter } from "./routes/ml.route.js";
import { authRouter } from "./routes/auth.route.js";
import { userRouter } from "./routes/user.route.js";
import { productRouter } from "./routes/product.route.js";
import { categoryRouter } from "./routes/category.route.js";
import { subcategoryRouter } from "./routes/subcategory.route.js";
import { orderRouter } from "./routes/order.route.js";
import { reviewRouter } from "./routes/review.route.js";
import { StatusCodes } from "http-status-codes";


export const app = express();

/*
Security Middleware
*/
app.use(helmet());

/*
CORS
*/
app.use(corsMiddleware);

/*
Performance & Parser
*/
app.use(compression());
app.use(cookieParser());
app.use(express.json());

/*
Security Headers & CSRF (handled by lusca)
*/
app.use(lusca.xframe("SAMEORIGIN"));
app.use(lusca.xssProtection(true));
// Note: CSRF is disabled by default here, enable if processing stateful forms with cookies
// app.use(lusca.csrf()); 

/*
HTTP Logger
*/
app.use(morgan("dev"));

/*
Static Files
*/
app.use("/uploads", express.static("uploads"));

/*
Routes
*/
app.use("/api/health", healthRouter);

// Apply rate limiter to all routes except health
app.use(rateLimitMiddleware);

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
  res.status(StatusCodes.NOT_FOUND).json({
    success: false,
    message: "Route not found",
  });
});

/*
Global Error Handler
*/
app.use(errorHandler);