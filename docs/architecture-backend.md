# Architecture Backend

```mermaid
graph TB
    subgraph "🚀 server.ts — Bootstrap"
        S1["bootstrap()"] --> S2["checkDatabaseConnection()<br/>SELECT NOW()"]
        S2 --> S3["app.listen(PORT, HOST)<br/>Banner + Graceful Shutdown"]
    end

    subgraph "⚙️ app.ts — Middleware Pipeline (ordre strict)"
        direction TB
        M1["1. requestIdMiddleware<br/>(UUID → req.id)"] 
        M2["2. requestLoggerMiddleware<br/>(metrics start timer + Pino log)"]
        M3["3. helmet()<br/>(XSS, Content-Security-Policy, etc)"]
        M4["4. corsMiddleware<br/>(origins depuis .env)"]
        M5["5. compression()<br/>(gzip)"]
        M6["6. cookieParser()"]
        M7["7. lusca<br/>(X-Frame-Options, XSS Protection)"]
        M8["8. express.static('/uploads')"]
        M9["9. Swagger UI<br/>(/api/docs + /api/docs.json)"]
        M10["10. rateLimitMiddleware<br/>100 req / 15 min"]
        M11["11. /api/health + /api/observability"]
        M12["12. voiceWebhookRouter<br/>(AVANT express.json → raw body)"]
        M13["13. csrfOriginMiddleware<br/>(Origin header check)"]
        M14["14. express.json()"]
        M15["15. Routes API"]
        M16["16. 404 Handler"]
        M17["17. errorHandler global"]
        M1 --> M2 --> M3 --> M4 --> M5 --> M6 --> M7 --> M8 --> M9 --> M10 --> M11 --> M12 --> M13 --> M14 --> M15 --> M16 --> M17
    end

    subgraph "🗂️ 13 Routes API"
        R1["/api/health GET"]
        R2["/api/auth register/login/logout"]
        R3["/api/users CRUD + profile"]
        R4["/api/products CRUD + search"]
        R5["/api/categories CRUD"]
        R6["/api/subcategories CRUD"]
        R7["/api/orders CRUD + status"]
        R8["/api/cart ajout/suppression"]
        R9["/api/reviews CRUD"]
        R10["/api/chat POST (proxy ML)"]
        R11["/api/ml price/features/models"]
        R12["/api/voice webhook/initiate/context"]
        R13["/api/observability health/metrics"]
    end

    subgraph "🔐 9 Middlewares"
        MW1["observability.middleware.ts<br/>req.id + metrics + logs"]
        MW2["cors.middleware.ts<br/>origins configurable"]
        MW3["csrf.middleware.ts<br/>Origin check si cookie JWT"]
        MW4["auth.middleware.ts<br/>JWT cookie → verify → DB check<br/>is_active + token_version"]
        MW5["role.middleware.ts<br/>authorize('admin','manager')"]
        MW6["validate.middleware.ts<br/>Zod body/query/params"]
        MW7["rateLimit.middleware.ts<br/>100 global / 10 auth"]
        MW8["upload.middleware.ts<br/>multer 8 files max 5MB<br/>magic number validation"]
        MW9["error.middleware.ts<br/>AppError / ZodError / JWT / DB"]
    end

    subgraph "🎮 12 Controllers"
        C1["health.controller"]
        C2["auth.controller"]
        C3["user.controller"]
        C4["product.controller"]
        C5["category.controller"]
        C6["subcategory.controller"]
        C7["order.controller"]
        C8["cart.controller"]
        C9["review.controller"]
        C10["chat.controller"]
        C11["ml.controller"]
        C12["voiceConfirmation.controller"]
    end

    subgraph "🧠 12 Services (Logique métier + SQL)"
        SV1["product.service<br/>slug, soft-delete, pagination"]
        SV2["auth.service<br/>bcrypt, JWT, token rotation"]
        SV3["order.service<br/>stock check, total, status"]
        SV4["cart.service<br/>stock + active check"]
        SV5["category.service"]
        SV6["subcategory.service"]
        SV7["review.service"]
        SV8["user.service"]
        SV9["chat.service<br/>proxy → ml:8000"]
        SV10["ml.service<br/>proxy /price/predict"]
        SV11["phoneConfirmation.service<br/>Retell AI + HMAC"]
        SV12["voice/ service"]
    end

    subgraph "📐 9 Validators (Zod)"
        V1["auth.schema"]
        V2["user.schema"]
        V3["product.schema"]
        V4["category.schema"]
        V5["subcategory.schema"]
        V6["order.schema"]
        V7["cart.schema"]
        V8["review.schema"]
        V9["payment.schema"]
    end

    subgraph "📦 Utils"
        U1["apiResponse.ts<br/>sendResponse() standardisé"]
        U2["AppError.ts<br/>statusCode + isOperational"]
        U3["logger.ts<br/>Pino structuré"]
        U4["metrics.ts<br/>prom-client (Counter, Histogram, Gauge)"]
        U5["password.ts<br/>bcrypt"]
    end

    subgraph "⚡ Data Layer"
        D1["db/pool.ts<br/>pg Pool → DATABASE_URL"]
        D2["db/dbCheck.ts<br/>SELECT NOW()"]
    end

    subgraph "🔧 Config"
        CF1["config/env.ts<br/>Zod validation + .env auto-load"]
        CF2["config/swagger.ts<br/>OpenAPI 3.0 complet"]
        CF3["config/trustProxy.ts"]
    end

    subgraph "📁 SQL Migrations (13 fichiers)"
        SQL1["001_tables.sql<br/>categories, products, users, orders..."]
        SQL2["002_constraints.sql<br/>FK, UNIQUE, CHECK"]
        SQL3["003_indexes.sql<br/>HNSW vector index"]
        SQL4["004_triggers.sql<br/>updated_at, order_total, review_stats"]
        SQL5["005_views.sql<br/>product_review_summary, order_summary"]
        SQL6["006_ml_schema.sql<br/>ml_models, user_features, segments"]
        SQL7["006b_ml_constraints.sql"]
        SQL8["007_ml_views.sql<br/>v_user_behavior_features"]
        SQL9["008_ml_indexes.sql"]
        SQL10["009_nlp_schema.sql<br/>chatbot_interactions"]
        SQL11["010_nlp_evaluations.sql<br/>nlp_similarity_metrics"]
        SQL12["011_fts_search.sql<br/>tsvector + GIN"]
        SQL13["012_voice_confirmations_extend.sql"]
        SQL14["013_price_drivers.sql"]
    end

    S3 --> M1
    M15 --> R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9 & R10 & R11 & R12 & R13
    R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9 & R10 & R11 & R12 & R13 --> C1 & C2 & C3 & C4 & C5 & C6 & C7 & C8 & C9 & C10 & C11 & C12
    C1 & C2 & C3 & C4 & C5 & C6 & C7 & C8 & C9 & C10 & C11 & C12 --> SV1 & SV2 & SV3 & SV4 & SV5 & SV6 & SV7 & SV8 & SV9 & SV10 & SV11 & SV12
    SV1 & SV2 & SV3 & SV4 & SV5 & SV6 & SV7 & SV8 & SV9 & SV10 & SV11 & SV12 --> D1
    D1 --> D2
    M17 --> U1 & U2 & U3 & U4 & U5

    M17 -.->|SQL migrations exécutées<br/>via npm run db:init| SQL1 & SQL2 & SQL3 & SQL4 & SQL5 & SQL6 & SQL7 & SQL8 & SQL9 & SQL10 & SQL11 & SQL12 & SQL13 & SQL14
    M15 -.->|validation Zod| V1 & V2 & V3 & V4 & V5 & V6 & V7 & V8 & V9
    M1 & M2 & M3 & M4 & M5 & M6 & M7 & M8 & M9 & M10 & M11 & M12 & M13 & M14 --> MW1 & MW2 & MW3 & MW4 & MW5 & MW6 & MW7 & MW8 & MW9
    CF1 & CF2 & CF3 -.-> M1
```

## Flux d'une requête typique (ex: GET /api/products)

```
Client HTTP
   │
   ▼
requestIdMiddleware      → req.id = UUID
requestLoggerMiddleware  → démarre timer + metrics
helmet()                 → ajoute en-têtes sécurité
corsMiddleware           → vérifie Origin
compression()            → gzip prêt
cookieParser()           → parse cookies
lusca                    → X-Frame, XSS
rateLimitMiddleware      → -1 dans le compteur
healthRouter NON         → pas /api/health
voiceWebhookRouter NON   → pas /api/voice/webhook
csrfOriginMiddleware     → GET = safe, next()
express.json()           → parse body
   │
   ▼
productRouter.GET '/'
   │
   ▼
validate({ query })     → Zod parse les query params
   │
   ▼
productController.getAllProducts(req, res, next)
   │
   ▼
productService.getAllProducts(filters)
   │
   ▼
pool.query(SQL)         → PostgreSQL
   │
   ▼
sendResponse(res, 200, "Products retrieved", { products, pagination })
   │
   ▼
requestLoggerMiddleware (on finish) → stop timer + log + metrics.update()
   │
   ▼
Client HTTP ← JSON { success, message, data }
```

## Fichiers clés

```
backend/
├── src/
│   ├── server.ts              → point d'entrée (bootstrap, graceful shutdown)
│   ├── app.ts                 → pipeline Express (ordre des middlewares)
│   ├── config/
│   │   ├── env.ts             → validation Zod des variables d'environnement
│   │   └── swagger.ts         → spec OpenAPI 3.0 complete (~986 lignes)
│   ├── db/
│   │   ├── pool.ts            → connexion PostgreSQL (pg Pool)
│   │   └── dbCheck.ts         → health check DB au démarrage
│   ├── middlewares/
│   │   ├── auth.middleware.ts → JWT cookie → verify → DB → req.user
│   │   ├── role.middleware.ts → authorize('admin', ...)
│   │   ├── validate.middleware.ts → Zod validation
│   │   ├── csrf.middleware.ts → Origin header check
│   │   ├── cors.middleware.ts → CORS dynamique
│   │   ├── rateLimit.middleware.ts → express-rate-limit
│   │   ├── upload.middleware.ts → multer + magic number
│   │   ├── error.middleware.ts → handler global
│   │   └── observability.middleware.ts → metrics + logs
│   ├── controllers/           → 12 controllers (orchestration req/res)
│   ├── services/              → 12 services (logique métier + SQL)
│   ├── validators/            → 9 schemas Zod
│   ├── routes/                → 13 route files
│   ├── sql/                   → 13 migrations SQL
│   ├── types/express.d.ts     → augmentation Express.Request
│   └── utils/                 → 5 utilitaires (metrics, logger, AppError, apiResponse, password)
```
