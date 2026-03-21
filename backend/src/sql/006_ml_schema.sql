-- ==========================================
-- ML MODELS & USER SEGMENTATION SCHEMA
-- ==========================================

-- 1. Table for ML Model Metadata
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(120) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- e.g., 'segmentation', 'recommendation'
    algorithm VARCHAR(50) NOT NULL,  -- e.g., 'K-Means', 'DBSCAN', 'RFM'
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_path TEXT, -- Path to the saved model file (e.g., S3 or local path)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_model_version UNIQUE(model_name, model_version)
);

-- 2. Table for User Features (Flat table for ML input)
CREATE TABLE IF NOT EXISTS user_features (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    
    -- Order Aggregations
    total_orders INTEGER NOT NULL DEFAULT 0,
    total_spent NUMERIC(12,2) NOT NULL DEFAULT 0,
    avg_order_value NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_items_bought INTEGER NOT NULL DEFAULT 0,
    
    -- Interaction Aggregations
    views_count INTEGER NOT NULL DEFAULT 0,
    clicks_count INTEGER NOT NULL DEFAULT 0,
    cart_add_count INTEGER NOT NULL DEFAULT 0,
    wishlist_add_count INTEGER NOT NULL DEFAULT 0,
    purchase_interaction_count INTEGER NOT NULL DEFAULT 0,
    search_count INTEGER NOT NULL DEFAULT 0,
    share_count INTEGER NOT NULL DEFAULT 0,
    
    -- Other Aggregations
    reviews_count INTEGER NOT NULL DEFAULT 0,
    avg_rating_given NUMERIC(3,2) NOT NULL DEFAULT 0,
    wishlist_count INTEGER NOT NULL DEFAULT 0,
    cart_count INTEGER NOT NULL DEFAULT 0,
    
    -- Recency & History
    days_since_last_order INTEGER,
    days_since_last_interaction INTEGER,
    days_since_signup INTEGER,
    
    -- Behavioral Ratios
    purchase_to_view_ratio NUMERIC(10,4) NOT NULL DEFAULT 0, -- Conversion rate
    cart_to_click_ratio NUMERIC(10,4) NOT NULL DEFAULT 0,
    review_to_purchase_ratio NUMERIC(10,4) NOT NULL DEFAULT 0,
    
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Table for User Segments (ML outputs)
CREATE TABLE IF NOT EXISTS user_segments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    segment_id INTEGER NOT NULL, -- Numeric ID from clustering (e.g., 0, 1, 2)
    segment_label VARCHAR(100),  -- Readable name (e.g., 'VIP', 'Churn Risk', 'Newcomer')
    model_name VARCHAR(120) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    confidence NUMERIC(6,4), -- Accuracy/probability score for the cluster assignment
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_model_assignment UNIQUE(user_id, model_name, model_version)
);

-- Bonus: User Sessions Table
-- Purpose: Tracking session duration, entry points, and device types allows for much finer segmentation
-- (e.g., separating "mobile browsers" from "desktop power users", or "high-intent search traffic" from "social media window shoppers").
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_started_at TIMESTAMPTZ NOT NULL,
    session_ended_at TIMESTAMPTZ,
    device_type VARCHAR(50), -- mobile, desktop, tablet
    source_channel VARCHAR(50), -- direct, organic, social, ads
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
