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
| **Helmet / CORS / Lusca / express-rate-limit / csurf** | Security (headers, CORS, CSRF, rate limiting) |
| **Pino** | Structured JSON logging |
| **prom-client** | Prometheus metrics (`/api/observability/metrics`) |
| **Prometheus + Alertmanager + Grafana** | Metrics collection, alerting, dashboards (`docker-compose`) |
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

## Use Case Diagrams

### Hiérarchie des acteurs

```mermaid
graph LR
    G[Guest] --> C[Customer]
    C --> A[Admin]
    C --> M[Manager]
```

### 1. Authentification et Navigation (Guest)

```mermaid
graph TD
    Guest([Guest]) --> U1["S'inscrire"]
    Guest --> U2[Se connecter]
    Guest --> U3[Consulter produits]
    Guest --> U4[Rechercher produits]
    Guest --> U5[Voir detail produit]
    Guest --> U6[Voir categories]
    Guest --> U7[Voir sous-categories]
    Guest --> U8[Voir avis produit]
```

### 2. Profil, Achats et Chat (Customer)

```mermaid
graph TD
    Customer([Customer]) --> U1[Voir mon profil]
    Customer --> U2[Modifier mon profil]
    Customer --> U3[Se deconnecter]
    Customer --> U4[Ajouter un avis]
    Customer --> U5[Modifier son avis]
    Customer --> U6[Supprimer son avis]
    Customer --> U7[Creer commande]
    Customer --> U8[Voir mes commandes]
    Customer --> U9[Voir detail commande]
    Customer --> U10[Chat AI assistant]

    U7 -.-> U11["Journaliser audit (<<include>>)"]
    U10 -.-> U12["Traiter chat RAG (<<include>>)"]
```

### 3. Gestion Utilisateurs (Admin)

```mermaid
graph TD
    Admin([Admin]) --> U1[Inscrire un admin]
    Admin --> U2[Lister utilisateurs]
    Admin --> U3[Voir utilisateur]
    Admin --> U4[Desactiver utilisateur]
    Admin --> U5[Changer role]
    Admin --> U6[Activer/desactiver compte]

    U4 -.-> U7["Journaliser audit (<<include>>)"]
```

### 4. Gestion Catalogue (Admin)

```mermaid
graph TD
    Admin([Admin]) --> U1[Creer produit]
    Admin --> U2[Modifier produit]
    Admin --> U3[Supprimer produit]
    Admin --> U4[Creer categorie]
    Admin --> U5[Modifier categorie]
    Admin --> U6[Supprimer categorie]
    Admin --> U7[Creer sous-categorie]
    Admin --> U8[Modifier sous-categorie]
    Admin --> U9[Supprimer sous-categorie]

    U1 -.-> U10["Journaliser audit (<<include>>)"]
    U2 -.-> U10
    U3 -.-> U10
```

### 5. Gestion Commandes (Admin)

```mermaid
graph TD
    Admin([Admin]) --> U1[Voir toutes commandes]
    Admin --> U2[MAJ statut commande]
    Admin --> U3[Annuler commande]

    U2 -.-> U4["Journaliser audit (<<include>>)"]
```

### 6. Machine Learning (Admin → ML Service)

```mermaid
graph TD
    Admin([Admin]) --> U1[Enregistrer modele ML]
    Admin --> U2[Predire prix produit]
    Admin --> U3[Recalculer features]
    Admin --> U4[Pousser segments]

    ML[/ML Service Python/]
    U2 -.->|<<include>>| ML
    U3 -.->|<<include>>| ML
    U4 -.->|<<include>>| ML
```

### 7. Confirmation Vocale (Admin → Retell AI)

```mermaid
graph TD
    Admin([Admin]) --> U1[Lancer appel vocal]
    Admin --> U2[Voir contexte appel]

    Sys([System]) --> U3[Passer appel Retell]
    Sys --> U4[Recevoir webhook Retell]
    Sys --> U5[Relancer appel si no-answer]
    Sys --> U6[Journaliser audit]

    Retell[/Retell AI/]
    U1 -.->|<<include>>| U3
    U1 -.->|<<include>>| U6
    U3 -.->|<<extend>>| U4
    U4 -.->|<<include>>| U2
    U4 -.->|<<extend>>| U5
    Retell -->|POST /api/voice/webhook| U4
```

### 8. Processus Automatiques Base de Données (System)

```mermaid
graph LR
    subgraph Triggers PostgreSQL
        T1[MAJ updated_at]
        T2[MAJ total_amount orders]
        T3[MAJ rating_avg / review_count]
    end
```

### Tables des acteurs

| Acteur | Rôle |
|--------|------|
| `Guest` | Non authentifié — navigation catalogue, auth |
| `Customer` | Authentifié (role `customer`) — achats, avis, chat |
| `Admin` | Role `admin` — gestion utilisateurs, produits, commandes, ML, appels vocaux |
| `Manager` | Role `manager` — hérite de Customer (réservé usage futur) |
| `Retell AI` | Service externe — POSTe le webhook de fin d'appel |
| `ML Service` | Service Python — calcul features, segmentation, prédiction prix |
| `System` | Backend + PostgreSQL — processus automatiques, appels externes |

### Légende des relations

| Symbole | Signification |
|---------|---------------|
| `A --> B` | L'acteur A déclenche le cas d'utilisation B |
| `A -.->\|<<include>>\| B` | A inclut obligatoirement B |
| `A -.->\|<<extend>>\| B` | A peut optionnellement étendre vers B |

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

## Observability

### Endpoints

| Path | Description |
| ---- | ----------- |
| `GET /api/observability/health` | Health check enrichi (statut DB + pool stats) |
| `GET /api/observability/metrics` | Métriques Prometheus (counter, histogram, gauge, métriques Node.js) |

### Métriques exposées

| Métrique | Type | Labels |
| -------- | ---- | ------ |
| `http_requests_total` | Counter | method, route, status_code |
| `http_request_duration_seconds` | Histogram (buckets: 5ms→10s) | method, route, status_code |
| `http_requests_active` | Gauge | method |
| `nodejs_*` (event loop, mémoire, GC, handles) | Gauges / Histograms | — |

### Stack technique

- **Pino** — Logger structuré JSON (pretty-print en dev, silencieux en test)
- **prom-client** — Métriques Prometheus embarquées dans le processus Node.js
- **Prometheus** — Scrape les métriques du backend toutes les 15s
- **Grafana** — Dashboards pré-configurés (req/s, latence, mémoire, event loop)

### Lancer la stack monitoring complète (Prometheus + Grafana + Alertmanager)

```bash
# Depuis backend/infra/docker/
docker compose up -d prometheus grafana alertmanager
```

### Services

| Service | URL | Rôle |
| ------- | --- | ---- |
| **Prometheus** | `http://localhost:9090` | Collecte et stocke les métriques (scrape toutes les 15s) |
| **Grafana** | `http://localhost:3000` | Visualisation des métriques (login: `admin` / `admin`) |
| **Alertmanager** | `http://localhost:9093` | Gère les alertes et les notifications (email, Slack, etc.) |

#### Pourquoi ces services ?

- **Prometheus** — Base de données de séries temporelles. Il **pull** (scrape) les métriques depuis le endpoint `/api/observability/metrics` du backend toutes les 15s et les stocke dans son TSDB. C'est le cœur du monitoring : sans lui, pas de données historiques, pas d'alertes.

- **Grafana** — Interface de dashboarding. Il interroge Prometheus en PromQL pour afficher des graphiques temps réel (requêtes/sec, latence, mémoire, event loop). Les dashboards sont **pré-provisionnés** (fichiers JSON versionnés dans le repo) — aucun clic manuel nécessaire.

- **Alertmanager** — Routage et notification des alertes. Il reçoit les alertes déclenchées par Prometheus et les envoie par **email** (ou Slack, Telegram, PagerDuty, etc.). Sans lui, les alertes restent dans Prometheus sans jamais notifier personne.

### Alertes pré-configurées (13 règles)

Les règles sont définies dans `infra/docker/prometheus/alert.rules.yml` et évaluées toutes les 15s :

| Alerte | Seuil | Sévérité | Déclencheur |
| ------ | ----- | -------- | ----------- |
| **BackendDown** | `up == 0` | 🔴 critical | Backend injoignable par Prometheus |
| **DatabaseUnreachable** | `503 sur /health` | 🔴 critical | PostgreSQL déconnecté |
| **MLServiceUnavailable** | `502/503/504 sur /api/ml/*` | 🔴 critical | Service ML (price prediction/segments) HS |
| **ChatMLServiceUnavailable** | `502/503/504 sur /api/chat` | 🔴 critical | Chat ML HS |
| **HighErrorRate** | `5xx > 5% des requêtes` | 🟡 warning | Bugs applicatifs généralisés |
| **BruteForceAttempt** | `401 login > 10/2min` | 🟡 warning | Attaque par force brute suspectée |
| **AuthRateLimitReached** | `429 auth` | 🟡 warning | Limiteur anti-brute-force qui bloque des requêtes légitimes |
| **OrderCreationFailing** | `400 POST /orders > 2/10min` | 🟡 warning | Stock épuisé ou produit inactif |
| **StockExhaustion** | `400 POST /cart > 5/10min` | 🟡 warning | Ajouts au panier refusés pour stock insuffisant |
| **HighP99Latency** | `P99 > 3s` | 🟡 warning | Latence dégradée |
| **HighP95Latency** | `P95 > 1s` | 🟡 warning | Latence dégradée |
| **MemoryPressure** | `heap > 85%` | 🟡 warning | Fuite mémoire possible |
| **AccountDeactivated** | `403 login > 2/5min` | 🔵 info | Comptes désactivés sollicités |
| **AdminSelfModificationAttempt** | `403 role/status` | 🔵 info | Admin tente de modifier son propre rôle |

Les alertes **critical** sont envoyées par email toutes les 30min, les **warning** toutes les 2h, les **info** toutes les 4h.

### Architecture

```mermaid
graph LR
    Backend[Node.js Backend<br/>:5000] -->|GET /api/observability/metrics| Backend
    Prometheus[Prometheus<br/>:9090] -->|scrape 15s| Backend
    Prometheus -->|alert rules| Alertmanager[Alertmanager<br/>:9093]
    Alertmanager -->|SMTP| Email[✉️ admin@email]
    Grafana[Grafana<br/>:3000] -->|query| Prometheus
    Dev[Developer] -->|http://localhost:3000| Grafana
```

### Fichiers de configuration

```
infra/docker/
  docker-compose.yml              ← Services: postgres, elasticsearch, kibana, logstash, prometheus, grafana, alertmanager
  prometheus/
    prometheus.yml                ← Scrape config + alerting rules + alertmanager target
    alert.rules.yml               ← 13 règles d'alerte métier (créé)
  alertmanager/
    alertmanager.yml              ← Configuration SMTP + routage des alertes (créé)
  grafana/
    datasources/
      datasource.yml              ← Auto-provision Prometheus datasource
    dashboards/
      dashboard.yml               ← Auto-provision dashboard provider
      nodejs-app.json             ← Dashboard JSON corrigé (6 panels + metric name fix)
```

### Commandes utiles

```bash
# Lancer toute la stack monitoring
docker compose up -d prometheus grafana alertmanager

# Vérifier l'état des conteneurs
docker ps

# Voir les alertes dans Prometheus
open http://localhost:9090/alerts

# Voir l'interface Alertmanager
open http://localhost:9093

# Voir le dashboard Grafana
open http://localhost:3000/dashboards

# Consulter les logs d'un service
docker logs ecommerce_alertmanager
docker logs ecommerce_prometheus
```

> **Note :** Pour recevoir les alertes par email, modifie les paramètres SMTP dans `infra/docker/alertmanager/alertmanager.yml` (smarthost, auth_username, auth_password, from, to).

## Security

- **Helmet** — HTTP headers hardening
- **CORS** — Restricted to `FRONTEND_URL` + `CORS_ALLOWED_ORIGINS`
- **CSRF** — Origin header validation via custom middleware on mutating requests
- **Rate limiting** — Auth endpoints (configurable via express-rate-limit)
- **JWT** — httpOnly cookie (`access_token`), not accessible from JS
- **Password** — bcryptjs with salt rounds
- **Zod validation** — All request bodies validated at runtime
- **Input sanitization** — Parameterized queries via pg
- **Production guards** — Enforces min 32-char JWT secret, webhook secret, and ML token

