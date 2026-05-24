-- ==========================================
-- PERFORMANCE INDEXES FOR ANALYTICAL VIEW (ML SPECIFIC)
-- ==========================================

-- User Interactions are high volume, indexing interaction_type and created_at helps filtering for ML windows
CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_user_interactions_created_at ON user_interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_price_predictions_product_created ON product_price_predictions(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_predictions_model ON product_price_predictions(model_name, model_version);
-- Cross-joins/Aggregations lookups are handled by base indexes in 003_indexes.sql
