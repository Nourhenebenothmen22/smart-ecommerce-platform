-- ==========================================
-- 009 NLP & CHATBOT SCHEMA
-- ==========================================

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Note: product_embeddings table is defined in 001_tables.sql

-- 2. Table for Chatbot Interaction Logs (Traceability)
CREATE TABLE IF NOT EXISTS chatbot_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(100), -- To track multiple turns in a conversation
    
    -- Request
    user_query TEXT NOT NULL,
    
    -- RAG Details (Retrieval)
    retrieval_algorithm VARCHAR(50), -- e.g., 'BM25', 'Dense_Cosine', 'Hybrid'
    retrieved_context JSONB, -- The products or reviews retrieved from DB to form the context
    
    -- LLM Inference
    llm_prompt TEXT, -- The exact prompt sent to the LLM (for debugging)
    llm_response TEXT NOT NULL,
    llm_model_used VARCHAR(100), -- e.g., 'gpt-4-turbo', 'llama-3-8b'
    
    -- Metrics
    execution_time_ms INTEGER, -- Total latency for retrieval + generation
    user_feedback_score INTEGER CHECK (user_feedback_score IN (1, -1, 0)), -- Thumbs up (1) / Thumbs down (-1)
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Note: In PostgreSQL, BM25-like behavior can be achieved via tsvector & tsquery (Full Text Search).
-- We will add a tsvector column to products in the future if we choose to run BM25 fully inside Postgres,
-- or handle BM25 via Python (e.g. using `rank_bm25` or ElasticSearch). For now, we rely on standard Postgres FTS or Python.
