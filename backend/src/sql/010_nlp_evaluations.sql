-- ==========================================
-- 010 NLP ALGORITHM EVALUATION SCHEMA
-- ==========================================

-- Table to store comparison metrics between different similarity algorithms
-- (e.g., BM25 vs Dense Cosine vs Hybrid Search)
CREATE TABLE IF NOT EXISTS nlp_similarity_metrics (
    id SERIAL PRIMARY KEY,
    
    experiment_name VARCHAR(120) NOT NULL, -- e.g., 'Search_Query_Evaluation_v1'
    dataset_size INTEGER NOT NULL, -- Number of queries tested
    
    algorithm_name VARCHAR(50) NOT NULL, -- 'BM25', 'Embedding_Cosine', 'TF-IDF'
    model_version VARCHAR(50), -- e.g., 'all-MiniLM-L6-v2' for embeddings
    
    -- Quantitative Metrics
    precision_at_k NUMERIC(6,4), -- E.g. Precision@5
    recall_at_k NUMERIC(6,4),    -- E.g. Recall@5
    mrr NUMERIC(6,4),            -- Mean Reciprocal Rank
    ndcg NUMERIC(6,4),           -- Normalized Discounted Cumulative Gain
    
    -- Operational Metrics
    avg_latency_ms NUMERIC(8,2), -- Average search time
    
    hyperparameters JSONB, -- Additional configs (e.g. chunk size, BM25 k1/b)
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
