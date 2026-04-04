# 🛡️ Backend Security Guide

This document details the security layers implemented in the **E-Commerce Intelligent Platform** backend.

---

## 🔐 1. Authentication & Session Management
- **JWT (JSON Web Tokens)**: Used for stateless authentication.
- **HTTP-Only Cookies**: Tokens are stored in HTTP-Only cookies to prevent XSS-based token theft.
- **Path Isolation**: The authentication middleware ([`auth.middleware.ts`](file:///c:/full_stack%20projects/ecommerce-intelligent-platform/backend/src/middlewares/auth.middleware.ts)) is applied globally to protected routes.

---

## 🛡️ 2. Defense in Depth (Middleware)
We use a multi-layered middleware stack to protect the API:

### 🚀 Helmet
Sets various HTTP headers to help protect against common web vulnerabilities (XSS, Clickjacking, MIME-sniffing, etc.).

### 🛡️ Lusca
Provides additional security headers:
- **X-Frame-Options**: Set to `SAMEORIGIN` to prevent clickjacking.
- **XSS Protection**: Forced to `true`.

### 🚦 Rate Limiting
Prevents brute-force attacks and DoS by limiting requests per IP:
- **Default**: 100 requests per 15 minutes.
- **Configuration**: Managed in [`rateLimit.middleware.ts`](file:///c:/full_stack%20projects/ecommerce-intelligent-platform/backend/src/middlewares/rateLimit.middleware.ts).

---

## ⚙️ 3. Input Validation & Environment
- **Zod Schema Validation**:
    - **Environment**: All `.env` variables are validated at startup using Zod ([`env.ts`](file:///c:/full_stack%20projects/ecommerce-intelligent-platform/backend/src/config/env.ts)).
    - **Request Body**: (In progress) Routes will use Zod schemas to ensure strict typing of incoming data.
- **SQL Injection Prevention**: All database queries use **parameterized queries** via `pg` (node-postgres), never string concatenation.

---

## 🚨 4. Centralized Error Handling
The [`AppError`](file:///c:/full_stack%20projects/ecommerce-intelligent-platform/backend/src/utils/AppError.ts) class and the global [`errorHandler`](file:///c:/full_stack%20projects/ecommerce-intelligent-platform/backend/src/middlewares/error.middleware.ts) ensure that:
1.  **Operational errors** are returned with standard HTTP status codes.
2.  **Sensitive info** (like stack traces) is HIDDEN in production.
3.  **Consistent Format**: All errors follow the `{ success: false, message, errors }` format.

---

## 📦 5. Dependencies
We use **Husky** and **Lint-staged** to ensure that:
- Code is formatted correctly.
- Critical tests pass before any commit is allowed.
- Environment secrets are NOT committed (see `.gitignore`).
