-- ==========================================
-- 011 FULL-TEXT SEARCH OPTIMIZATION
-- Adds a pre-computed tsvector column + GIN index
-- for high-performance BM25/FTS queries.
-- ==========================================

-- 1. Add tsvector column to products
ALTER TABLE products ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 2. Create trigger to auto-update search_vector on INSERT/UPDATE
CREATE OR REPLACE FUNCTION products_search_vector_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('french',
        COALESCE(NEW.title, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.brand, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_products_search_vector ON products;
CREATE TRIGGER trg_products_search_vector
    BEFORE INSERT OR UPDATE OF title, description, brand ON products
    FOR EACH ROW EXECUTE FUNCTION products_search_vector_update();

-- 3. Backfill existing rows
UPDATE products SET search_vector = to_tsvector('french',
    COALESCE(title, '') || ' ' ||
    COALESCE(description, '') || ' ' ||
    COALESCE(brand, '')
)
WHERE search_vector IS NULL;

-- 4. Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_products_search_fts ON products USING GIN (search_vector);
