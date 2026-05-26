-- Add price driver columns to products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS supplier_cost NUMERIC(10,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS margin_pct NUMERIC(5,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand_tier INTEGER DEFAULT 2;        -- 1=budget, 2=mid, 3=premium, 4=luxury
ALTER TABLE products ADD COLUMN IF NOT EXISTS product_tier INTEGER DEFAULT 2;      -- 1=entry, 2=mid, 3=high, 4=flagship
ALTER TABLE products ADD COLUMN IF NOT EXISTS condition VARCHAR(20) DEFAULT 'new'; -- new, refurbished, open_box, used
ALTER TABLE products ADD COLUMN IF NOT EXISTS release_year INTEGER;
