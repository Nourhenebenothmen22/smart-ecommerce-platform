# Backend — E-Commerce Intelligent Platform

## Overview

Express.js backend with PostgreSQL (pgvector), JWT auth, Swagger docs, ML integration (segmentation / price prediction), and phone order confirmation via Retell AI.

## Tech Stack

| Dep | Role |
| --- | ---- |
| **Express 5** | HTTP framework |
| **TypeScript 5 + tsx** | Dev server / watch |
| **pg** (node-postgres) | PostgreSQL client |
| **pgvector** | Vector embeddings (384d) |
| **Zod** | Runtime schema validation |
| **JWT** (jsonwebtoken) | Auth (httpOnly cookie) |
| **bcryptjs** | Password hashing |
| **Swagger** (swagger-jsdoc + swagger-ui-express) | OpenAPI 3.0 docs |
| **Helmet / CORS / Lusca (CSRF) / express-rate-limit** | Security |
| **Jest + ts-jest + supertest** | Testing (101 tests, 21 suites) |

## Setup

### Prerequisites

- Node.js ≥ 22
- Docker (PostgreSQL with pgvector)

### Install

```bash
cd backend
npm install
```

### Database

Start the PostgreSQL container:

```bash
docker run -d \
  --name ecommerce_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ecommerce_ml_db \
  -p 5433:5432 \
  ankane/pgvector:latest
```

Run all 15 migration files (idempotent):

```bash
npm run db:init
```

Or run individual migrations:

```bash
npm run db:1-tables      # Core tables + extensions
npm run db:2-constraints # FK, unique, check constraints
npm run db:3-indexes     # Performance + HNSW vector index
npm run db:4-triggers    # Auto-update timestamps, totals, review stats
npm run db:5-views       # product_review_summary, order_summary
npm run db:6-ml-schema   # ML tables (ml_models, user_features, etc.)
npm run db:6b-ml-constraints # ML traceability FKs
npm run db:7-ml-views    # v_user_behavior_features analytical view
npm run db:8-ml-indexes  # ML-specific indexes
npm run db:9-nlp-schema  # chatbot_interactions table
npm run db:10-nlp-evaluations # nlp_similarity_metrics table
npm run db:11-fts        # Full-text search (tsvector + GIN)
npm run db:12-voice-confirmations-extend # Voice confirmation extensions
npm run db:13-price-drivers # Price driver columns on products
```

### Environment

Copy the root `.env` (backend reads `.env` from the project root):

```env
PORT=5000
HOST=0.0.0.0
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/ecommerce_ml_db
JWT_SECRET=your-jwt-secret-min-32-chars-in-production
JWT_EXPIRES_IN=7d
NODE_ENV=development
FRONTEND_URL=http://localhost:5173
CORS_ALLOWED_ORIGINS=http://localhost:5000

# Retell AI (phone confirmation)
RETELL_API_KEY=
RETELL_AGENT_ID=
RETELL_FROM_NUMBER=
RETELL_WEBHOOK_SECRET=
WEBHOOK_BASE_URL=

# ML service (Python)
ML_SERVICE_URL=http://127.0.0.1:8000
ML_SERVICE_TOKEN=
ML_REQUEST_TIMEOUT_MS=5000

# Security
TRUST_PROXY=false
COOKIE_SECRET=
```

### Dev

```bash
npm run dev      # tsx watch on src/server.ts
```

Open **http://localhost:5000** (server responds)  
Open **http://localhost:5000/api/docs** (Swagger UI)

### Build & Start

```bash
npm run build    # tsc → dist/
npm start        # node dist/server.js
```

### Test

```bash
npm test         # jest --runInBand --passWithNoTests (101 tests)
```

## Scripts

| Command | Description |
| ------- | ----------- |
| `npm run dev` | Start dev server with hot-reload (tsx watch) |
| `npm run build` | Compile TS to JS (tsc) |
| `npm start` | Run compiled production server |
| `npm run lint` | Type-check without emitting (tsc --noEmit) |
| `npm test` | Run all Jest tests |
| `npm run db:init` | Run all 15 migration files sequentially |
| `npm run db:1-tables` … `db:13-price-drivers` | Individual migrations |
| `npm run ml:upsert-features` | Upsert user features from ML SQL |
| `npm run ml:seed:append` | Append seed data via ML Python script |
| `npm run ml:seed:reset` | Reset seed data via ML Python script |

## Project Structure

```
src/
  app.ts                    Express app setup (middleware, routes, error handler)
  server.ts                 Entry point (binds to HOST:PORT, startup banner)
  config/
    env.ts                  Zod schema for all env vars (validated at startup)
    swagger.ts              OpenAPI 3.0 spec (all paths, schemas, tags)
  db/
    pool.ts                 pg Pool singleton (reads DATABASE_URL)
    dbCheck.ts              DB connectivity check utility
  middlewares/
    auth.middleware.ts      JWT verification (extracts user from cookie)
    cors.middleware.ts      CORS configuration (FRONTEND_URL + CORS_ALLOWED_ORIGINS)
    csrf.middleware.ts      CSRF protection via Lusca
    error.middleware.ts     Global error handler
    rateLimit.middleware.ts Rate limiting (express-rate-limit)
    role.middleware.ts      Role-based access control (customer / admin / manager)
    upload.middleware.ts    Multer file upload (products images)
    validate.middleware.ts  Zod schema validation middleware
  controllers/              Request handlers (11 files)
  services/                 Business logic (11 files + voice/)
  routes/                   Express routers (11 files)
  validators/               Zod schemas (9 files)
  types/
    express.d.ts            Express Request augmentation (user payload)
  utils/
    apiResponse.ts          Unified { success, message, data, errors } response builder
    AppError.ts             Custom error class (status code, isOperational)
    password.ts             bcryptjs hash/compare helpers
  sql/                      15 migration SQL files (001–013)
  tests/                    22 test files + helpers/
```

## API Endpoints

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| **GET** | `/api/health` | — | Health check |
| **POST** | `/api/auth/register` | — | Register customer |
| **POST** | `/api/auth/register-admin` | admin | Register admin user |
| **POST** | `/api/auth/login` | — | Login |
| **POST** | `/api/auth/logout` | user | Logout |
| **GET** | `/api/users/me` | user | Current profile |
| **PATCH** | `/api/users/me` | user | Update profile |
| **GET** | `/api/users` | admin | List all users |
| **GET** | `/api/users/:id` | admin | Get user by ID |
| **DELETE** | `/api/users/:id` | admin | Deactivate user |
| **PATCH** | `/api/users/:id/role` | admin | Update user role |
| **PATCH** | `/api/users/:id/status` | admin | Toggle active status |
| **GET** | `/api/products` | — | List products (paginated, filterable) |
| **POST** | `/api/products` | admin | Create product |
| **GET** | `/api/products/:id` | — | Get product |
| **PATCH** | `/api/products/:id` | admin | Update product |
| **DELETE** | `/api/products/:id` | admin | Delete / deactivate product |
| **GET** | `/api/categories` | — | List categories |
| **POST** | `/api/categories` | admin | Create category |
| **GET** | `/api/categories/:id` | — | Get category |
| **PATCH** | `/api/categories/:id` | admin | Update category |
| **DELETE** | `/api/categories/:id` | admin | Delete category |
| **GET** | `/api/categories/:categoryId/subcategories` | — | Subcategories by category |
| **GET** | `/api/subcategories` | — | List subcategories |
| **POST** | `/api/subcategories` | admin | Create subcategory |
| **GET** | `/api/subcategories/:id` | — | Get subcategory |
| **PATCH** | `/api/subcategories/:id` | admin | Update subcategory |
| **DELETE** | `/api/subcategories/:id` | admin | Delete subcategory |
| **GET** | `/api/products/:productId/reviews` | — | Reviews for product |
| **POST** | `/api/reviews` | user | Add review |
| **GET** | `/api/reviews/product/:id` | — | Reviews by product (legacy) |
| **PATCH** | `/api/reviews/:id` | owner | Update review |
| **DELETE** | `/api/reviews/:id` | owner | Delete review |
| **POST** | `/api/orders` | user | Create order |
| **GET** | `/api/orders` | admin | List all orders |
| **GET** | `/api/orders/my` | user | My orders |
| **GET** | `/api/orders/:id` | owner/admin | Get order |
| **DELETE** | `/api/orders/:id` | admin | Cancel order |
| **PATCH** | `/api/orders/:id/status` | admin | Update order status |
| **POST** | `/api/ml/recalculate-features` | admin | Recalculate user features |
| **POST** | `/api/ml/segments` | admin | Push segmentation results |
| **POST** | `/api/ml/models` | admin | Register ML model |
| **POST** | `/api/ml/price/predict` | admin | Predict product price |
| **POST** | `/api/voice/initiate/:id` | admin | Initiate phone confirmation call |
| **GET** | `/api/voice/context/:id` | admin | Get call context |
| **POST** | `/api/voice/webhook` | — | Voice provider webhook (HMAC) |
| **POST** | `/api/chat` | customer | AI chatbot query |

## Database Tables

### Core Commerce

| Table | Key Columns |
| ----- | ----------- |
| `categories` | id, name, slug, description |
| `subcategories` | id, category_id, name, slug, description |
| `products` | id, title, slug, description, brand, category_id, subcategory_id, price, discount_percent, final_price (generated), rating_avg, review_count, stock, thumbnail, images (jsonb), tags (jsonb), is_active, search_vector (tsvector) |
| `users` | id, first_name, last_name, email (citext), password_hash, phone, address, city, postal_code, country, role, is_active, token_version |
| `reviews` | id, product_id, user_id, rating (1–5), review_text, verified_purchase |
| `cart_items` | id, user_id, product_id, quantity |
| `orders` | id, user_id, status, total_amount, payment_status |
| `order_items` | id, order_id, product_id, product_name_snapshot, quantity, unit_price, subtotal |
| `payments` | id, order_id, payment_method, amount, status, transaction_ref, paid_at |
| `wishlists` | id, user_id, product_id |
| `user_interactions` | id, user_id, product_id, interaction_type, interaction_value |
| `recommendations` | id, user_id, source_product_id, recommended_product_id, score |
| `audit_logs` | id, user_id, action, entity_type, entity_id, metadata (jsonb) |
| `user_sessions` | id, user_id, session_started_at, session_ended_at, device_type, source_channel |

### ML / NLP

| Table | Key Columns |
| ----- | ----------- |
| `ml_models` | id, model_name, model_version, model_type, algorithm, metrics (jsonb), parameters (jsonb), artifact_path, is_active, trained_at |
| `user_features` | id, user_id, total_orders, total_spent, avg_order_value, total_items_bought, views_count, clicks_count, cart_add_count, wishlist_add_count, purchase_interaction_count, search_count, share_count, reviews_count, avg_rating_given, wishlist_count, cart_count, days_since_last_order, days_since_last_interaction, days_since_signup, purchase_to_view_ratio, cart_to_click_ratio, review_to_purchase_ratio |
| `user_segments` | id, user_id, segment_id, segment_label, model_name, model_version, confidence |
| `product_embeddings` | id, product_id, model_name, model_version, embedding_vector (vector(384)) |
| `product_price_predictions` | id, product_id, predicted_price, currency, model_name, model_version, input_features (jsonb), metrics_snapshot (jsonb) |
| `review_analysis` | id, review_id, sentiment_label, sentiment_score, keywords (jsonb), topics (jsonb), model_name, model_version |
| `chatbot_interactions` | id, user_id, session_id, user_query, retrieval_algorithm, retrieved_context (jsonb), llm_prompt, llm_response, llm_model_used, execution_time_ms, user_feedback_score |
| `nlp_similarity_metrics` | id, experiment_name, dataset_size, algorithm_name, model_version, precision_at_k, recall_at_k, mrr, ndcg, avg_latency_ms, hyperparameters (jsonb) |
| `business_drivers` | (price driver columns added to products via 013) |

### Voice Confirmation

| Table | Key Columns |
| ----- | ----------- |
| `voice_confirmations` | id, order_id, phone_number, call_status, transcript, confirmed, confirmed_at, retry_count, provider_call_id |

### Views

| View | Description |
| ---- | ----------- |
| `product_review_summary` | Product ID, title, rating_avg, review_count, total_reviews |
| `order_summary` | Order ID, user_id, status, payment_status, total_amount, total_items |
| `v_user_behavior_features` | Full analytical view joining orders, items, reviews, interactions, wishlists, cart for ML input |

## ER Diagram

```mermaid
erDiagram
    categories ||--o{ subcategories : "has"
    categories ||--o{ products : "contains"
    subcategories ||--o{ products : "has"

    users ||--o{ reviews : "writes"
    users ||--o{ cart_items : "owns"
    users ||--o{ orders : "places"
    users ||--o{ wishlists : "has"
    users ||--o{ user_interactions : "performs"
    users ||--o{ user_features : "features"
    users ||--o{ user_segments : "segmented"
    users ||--o{ user_sessions : "sessions"
    users ||--o{ audit_logs : "audited"
    users ||--o{ chatbot_interactions : "chats"

    products ||--o{ reviews : "receives"
    products ||--o{ cart_items : "in"
    products ||--o{ order_items : "ordered"
    products ||--o{ wishlists : "wished"
    products ||--o{ user_interactions : "interacted"
    products ||--o{ recommendations : "source_or_target"
    products ||--o{ product_embeddings : "embedded"
    products ||--o{ product_price_predictions : "price_predicted"

    orders ||--o{ order_items : "contains"
    orders ||--|| payments : "has"
    orders ||--o{ voice_confirmations : "confirmed_via_phone"

    reviews ||--|| review_analysis : "analyzed"

    ml_models ||--o{ product_embeddings : "embedding_model"
    ml_models ||--o{ review_analysis : "analysis_model"
    ml_models ||--o{ user_segments : "segmentation_model"
    ml_models ||--o{ product_price_predictions : "price_prediction_model"
```

## Use Case Diagram

```mermaid
actor Guest
actor Customer
actor Admin
actor Manager
actor RetellAI as "Retell AI"
actor MLService as "ML Service"
actor System

Guest <|-- Customer
Customer <|-- Admin
Customer <|-- Manager

usecase U1 as "S'inscrire"
usecase U2 as "Se connecter"
usecase U3 as "Se deconnecter"
usecase U4 as "Consulter produits"
usecase U5 as "Rechercher produits"
usecase U6 as "Voir detail produit"
usecase U7 as "Voir categories"
usecase U8 as "Voir sous-categories"
usecase U9 as "Voir avis produit"
usecase U10 as "Voir mon profil"
usecase U11 as "Modifier mon profil"
usecase U12 as "Ajouter un avis"
usecase U13 as "Modifier son avis"
usecase U14 as "Supprimer son avis"
usecase U15 as "Creer commande"
usecase U16 as "Voir mes commandes"
usecase U17 as "Voir detail commande"
usecase U18 as "Chat AI assistant"
usecase U19 as "Inscrire un admin"
usecase U20 as "Lister utilisateurs"
usecase U21 as "Voir utilisateur"
usecase U22 as "Desactiver utilisateur"
usecase U23 as "Changer role"
usecase U24 as "Activer/desactiver compte"
usecase U25 as "Creer produit"
usecase U26 as "Modifier produit"
usecase U27 as "Supprimer produit"
usecase U28 as "Creer categorie"
usecase U29 as "Modifier categorie"
usecase U30 as "Supprimer categorie"
usecase U31 as "Creer sous-categorie"
usecase U32 as "Modifier sous-categorie"
usecase U33 as "Supprimer sous-categorie"
usecase U34 as "Voir toutes commandes"
usecase U35 as "MAJ statut commande"
usecase U36 as "Annuler commande"
usecase U37 as "Lancer appel vocal"
usecase U38 as "Voir contexte appel"
usecase U39 as "Enregistrer modele ML"
usecase U40 as "Predire prix produit"
usecase U41 as "Recalculer features"
usecase U42 as "Pousser segments"
usecase U43 as "Passer appel Retell"
usecase U44 as "Recevoir webhook"
usecase U45 as "Relancer appel"
usecase U46 as "Appeler ML Service"
usecase U47 as "Journaliser audit"
usecase U48 as "MAJ automatique timestamps"
usecase U49 as "MAJ automatique total_amount"
usecase U50 as "MAJ automatique rating_avg"
usecase U51 as "Traiter chat RAG"

Guest --> U1
Guest --> U2
Customer --> U3
Guest --> U4
Guest --> U5
Guest --> U6
Guest --> U7
Guest --> U8
Guest --> U9
Customer --> U10
Customer --> U11
Customer --> U12
Customer --> U13
Customer --> U14
Customer --> U15
Customer --> U16
Customer --> U17
Customer --> U18
Admin --> U19
Admin --> U20
Admin --> U21
Admin --> U22
Admin --> U23
Admin --> U24
Admin --> U25
Admin --> U26
Admin --> U27
Admin --> U28
Admin --> U29
Admin --> U30
Admin --> U31
Admin --> U32
Admin --> U33
Admin --> U34
Admin --> U35
Admin --> U36
Admin --> U37
Admin --> U38
Admin --> U39
Admin --> U40
Admin --> U41
Admin --> U42
System --> U43
System --> U44
System --> U45
System --> U46
System --> U47
System --> U48
System --> U49
System --> U50
System --> U51

U37 ..> U43 : <<include>>
U37 ..> U47 : <<include>>
U43 ..> U44 : <<extend>>
U44 ..> U45 : <<extend>>
U44 ..> U35 : <<include>>
U40 ..> U46 : <<include>>
U41 ..> U46 : <<include>>
U42 ..> U46 : <<include>>
U15 ..> U47 : <<include>>
U35 ..> U47 : <<include>>
U25 ..> U47 : <<include>>
U26 ..> U47 : <<include>>
U27 ..> U47 : <<include>>
U22 ..> U47 : <<include>>
U18 ..> U51 : <<include>>

RetellAI --> U44 : "POST webhook"
MLService --> U46 : "HTTP call"
```

| Acteur | Rôle |
|--------|------|
| Guest | Non authentifié — navigation catalogue, auth |
| Customer | Authentifié (role `customer`) — achats, avis, chat |
| Admin | Role `admin` — gestion utilisateurs, produits, commandes, ML, appels vocaux |
| Manager | Role `manager` — hérite de Customer (réservé usage futur) |
| Retell AI | Service externe — appelle `/api/voice/webhook` |
| ML Service | Service Python — calcul features, segmentation, prédiction prix |

| Stéréotype | Signification |
|------------|---------------|
| `<<include>>` | Le cas source déclenche obligatoirement le cas cible |
| `<<extend>>` | Le cas source peut optionnellement déclencher le cas cible |

## Migration Files Index

| # | File | Purpose |
| - | ---- | ------- |
| 001 | `001_tables.sql` | Extensions (vector, citext), all base tables |
| 002 | `002_constraints.sql` | FK, unique, check constraints |
| 003 | `003_indexes.sql` | FK indexes, status indexes, HNSW vector index |
| 004 | `004_triggers.sql` | `update_timestamp`, `maintain_order_total`, `maintain_product_review_stats` |
| 005 | `005_views.sql` | `product_review_summary`, `order_summary` |
| 006 | `006_ml_schema.sql` | `ml_models`, `user_features`, `user_segments`, `product_price_predictions`, `user_sessions` |
| 006b | `006b_ml_constraints.sql` | ML table foreign keys + check constraints |
| 007 | `007_ml_views.sql` | `v_user_behavior_features` analytical view |
| 008 | `008_ml_indexes.sql` | ML-specific indexes |
| 009 | `009_nlp_schema.sql` | `chatbot_interactions` (RAG + LLM traceability) |
| 010 | `010_nlp_evaluations.sql` | `nlp_similarity_metrics` (Precision@K, MRR, NDCG) |
| 011 | `011_fts_search.sql` | `search_vector` tsvector column + GIN index |
| 012 | `012_voice_confirmations_extend.sql` | retry_count, provider_call_id, partial unique index |
| 013 | `013_price_drivers.sql` | supplier_cost, margin_pct, brand_tier, product_tier, condition, release_year |

## Security

- **Helmet** — HTTP headers hardening
- **CORS** — Restricted to `FRONTEND_URL` + `CORS_ALLOWED_ORIGINS`
- **CSRF** — Lusca CSRF token validation on mutating requests
- **Rate limiting** — Auth endpoints (configurable via express-rate-limit)
- **JWT** — httpOnly cookie (`access_token`), not accessible from JS
- **Password** — bcryptjs with salt rounds
- **Zod validation** — All request bodies validated at runtime
- **Input sanitization** — Parameterized queries via pg
- **Production guards** — Enforces min 32-char JWT secret, webhook secret, and ML token

