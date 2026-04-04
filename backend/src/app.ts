import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import dotenv from "dotenv";
import compression from "compression";
import cookieParser from "cookie-parser";
import lusca from "lusca";
import { corsMiddleware } from "./middlewares/cors.middleware.js";
import { rateLimitMiddleware } from "./middlewares/rateLimit.middleware.js";
import { errorHandler } from "./middlewares/error.middleware.js";
import { healthRouter } from "./routes/health.route.js";
import { mlRouter } from "./routes/ml.route.js";
import { authRouter } from "./routes/auth.routes.js";
import { userRouter } from "./routes/user.routes.js";
import { productRouter } from "./routes/product.routes.js";
import { categoryRouter } from "./routes/category.routes.js";
import { subcategoryRouter } from "./routes/subcategory.routes.js";
import { orderRouter } from "./routes/order.routes.js";
import { reviewRouter } from "./routes/review.routes.js";
import { xssMiddleware } from "./middlewares/xss.middleware.js";


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
XSS Sanitization (Custom DOMPurify)
*/
app.use(xssMiddleware);

/*
HTTP Logger
*/
app.use(morgan("dev"));

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
  res.status(404).json({
    success: false,
    message: "Route not found",
  });
});

/*
Global Error Handler
*/
app.use(errorHandler);