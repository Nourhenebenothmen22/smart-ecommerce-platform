-- ==========================================
-- PERFORMANCE INDEXES FOR ANALYTICAL VIEW (ML SPECIFIC)
-- ==========================================

-- User Interactions are high volume, indexing interaction_type and created_at helps filtering for ML windows
CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_user_interactions_created_at ON user_interactions(created_at);
-- Cross-joins/Aggregations lookups are handled by base indexes in 003_indexes.sql
