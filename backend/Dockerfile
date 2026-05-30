FROM node:20-alpine AS builder
WORKDIR /app

COPY backend/package.json backend/package-lock.json ./
RUN npm ci --ignore-scripts

COPY backend/tsconfig.json ./
COPY backend/src/ ./src/

# Shared SQL script used by ML service
COPY ml/data/sql/upsert_user_features.sql ./ml/data/sql/upsert_user_features.sql

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 express

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
COPY --from=builder /app/ml/data/sql/upsert_user_features.sql ./ml/data/sql/upsert_user_features.sql

RUN mkdir -p uploads/products && chown -R express:nodejs uploads

USER express
EXPOSE 5000

ENV NODE_ENV=production
CMD ["node", "dist/server.js"]
