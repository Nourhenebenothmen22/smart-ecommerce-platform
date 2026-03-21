-- ==========================================
-- CONSTRAINTS : FOREIGN KEYS (IDEMPOTENT)
-- ==========================================

DO $$ 
BEGIN
    -- Subcategories -> Categories
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_subcat_category') THEN
        ALTER TABLE subcategories ADD CONSTRAINT fk_subcat_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
    END IF;

    -- Products -> Categories
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_prod_category') THEN
        ALTER TABLE products ADD CONSTRAINT fk_prod_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
    END IF;

    -- Subcategories (id, category_id) UNIQUE - Required for Products FK
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_subcategory_id_category') THEN
        ALTER TABLE subcategories ADD CONSTRAINT uq_subcategory_id_category UNIQUE (id, category_id);
    END IF;

    -- Products -> Subcategories (and Category matching)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_prod_subcategory_category') THEN
        ALTER TABLE products ADD CONSTRAINT fk_prod_subcategory_category FOREIGN KEY (subcategory_id, category_id) REFERENCES subcategories(id, category_id) ON DELETE RESTRICT;
    END IF;

    -- Reviews
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rev_product') THEN
        ALTER TABLE reviews ADD CONSTRAINT fk_rev_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rev_user') THEN
        ALTER TABLE reviews ADD CONSTRAINT fk_rev_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;

    -- Cart Items
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_cart_user') THEN
        ALTER TABLE cart_items ADD CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_cart_product') THEN
        ALTER TABLE cart_items ADD CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    END IF;

    -- Orders
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_ord_user') THEN
        ALTER TABLE orders ADD CONSTRAINT fk_ord_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
    END IF;

    -- Order Items
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_orditem_order') THEN
        ALTER TABLE order_items ADD CONSTRAINT fk_orditem_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_orditem_product') THEN
        ALTER TABLE order_items ADD CONSTRAINT fk_orditem_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;
    END IF;

    -- Payments
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_pay_order') THEN
        ALTER TABLE payments ADD CONSTRAINT fk_pay_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT;
    END IF;

    -- Interactions
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_uint_user') THEN
        ALTER TABLE user_interactions ADD CONSTRAINT fk_uint_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_uint_product') THEN
        ALTER TABLE user_interactions ADD CONSTRAINT fk_uint_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    END IF;

    -- Recommendations
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rec_user') THEN
        ALTER TABLE recommendations ADD CONSTRAINT fk_rec_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rec_src_product') THEN
        ALTER TABLE recommendations ADD CONSTRAINT fk_rec_src_product FOREIGN KEY (source_product_id) REFERENCES products(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rec_rec_product') THEN
        ALTER TABLE recommendations ADD CONSTRAINT fk_rec_rec_product FOREIGN KEY (recommended_product_id) REFERENCES products(id) ON DELETE CASCADE;
    END IF;

    -- ML Traceability (Composite FKs to ml_models)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_revanal_ml_model') THEN
        ALTER TABLE review_analysis ADD CONSTRAINT fk_revanal_ml_model FOREIGN KEY (model_name, model_version) REFERENCES ml_models(model_name, model_version) ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_prodembed_ml_model') THEN
        ALTER TABLE product_embeddings ADD CONSTRAINT fk_prodembed_ml_model FOREIGN KEY (model_name, model_version) REFERENCES ml_models(model_name, model_version) ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_usegs_ml_model') THEN
        ALTER TABLE user_segments ADD CONSTRAINT fk_usegs_ml_model FOREIGN KEY (model_name, model_version) REFERENCES ml_models(model_name, model_version) ON DELETE RESTRICT;
    END IF;

    -- Other ML FKs
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_revanal_review') THEN
        ALTER TABLE review_analysis ADD CONSTRAINT fk_revanal_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_prodembed_product') THEN
        ALTER TABLE product_embeddings ADD CONSTRAINT fk_prodembed_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_wish_user') THEN
        ALTER TABLE wishlists ADD CONSTRAINT fk_wish_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_wish_product') THEN
        ALTER TABLE wishlists ADD CONSTRAINT fk_wish_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_voice_order') THEN
        ALTER TABLE voice_confirmations ADD CONSTRAINT fk_voice_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_audit_user') THEN
        ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;

END $$;


-- ==========================================
-- CONSTRAINTS : UNIQUE (IDEMPOTENT)
-- ==========================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_category_slug') THEN
        ALTER TABLE categories ADD CONSTRAINT uq_category_slug UNIQUE (slug);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_subcategory_slug') THEN
        ALTER TABLE subcategories ADD CONSTRAINT uq_subcategory_slug UNIQUE (slug);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_product_slug') THEN
        ALTER TABLE products ADD CONSTRAINT uq_product_slug UNIQUE (slug);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_email') THEN
        ALTER TABLE users ADD CONSTRAINT uq_user_email UNIQUE (email);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_review_user_product') THEN
        ALTER TABLE reviews ADD CONSTRAINT uq_review_user_product UNIQUE (user_id, product_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_cart_user_product') THEN
        ALTER TABLE cart_items ADD CONSTRAINT uq_cart_user_product UNIQUE (user_id, product_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_orderitem_order_product') THEN
        ALTER TABLE order_items ADD CONSTRAINT uq_orderitem_order_product UNIQUE (order_id, product_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_payment_order') THEN
        ALTER TABLE payments ADD CONSTRAINT uq_payment_order UNIQUE (order_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_rec_user_source_rec') THEN
        ALTER TABLE recommendations ADD CONSTRAINT uq_rec_user_source_rec UNIQUE (user_id, source_product_id, recommended_product_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_revanal_review') THEN
        ALTER TABLE review_analysis ADD CONSTRAINT uq_revanal_review UNIQUE (review_id);
    END IF;
    
    -- Updated to include version
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_prodembed_product_model_v') THEN
        ALTER TABLE product_embeddings ADD CONSTRAINT uq_prodembed_product_model_v UNIQUE (product_id, model_name, model_version);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_wishlst_user_product') THEN
        ALTER TABLE wishlists ADD CONSTRAINT uq_wishlst_user_product UNIQUE (user_id, product_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_voice_order') THEN
        ALTER TABLE voice_confirmations ADD CONSTRAINT uq_voice_order UNIQUE (order_id);
    END IF;
END $$;


-- ==========================================
-- CONSTRAINTS : CHECK (IDEMPOTENT)
-- ==========================================

DO $$ 
BEGIN
    -- Products
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_product_price') THEN
        ALTER TABLE products ADD CONSTRAINT chk_product_price CHECK (price >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_product_discount') THEN
        ALTER TABLE products ADD CONSTRAINT chk_product_discount CHECK (discount_percent BETWEEN 0 AND 100);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_product_rating') THEN
        ALTER TABLE products ADD CONSTRAINT chk_product_rating CHECK (rating_avg BETWEEN 0.00 AND 5.00);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_product_review_count') THEN
        ALTER TABLE products ADD CONSTRAINT chk_product_review_count CHECK (review_count >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_product_stock') THEN
        ALTER TABLE products ADD CONSTRAINT chk_product_stock CHECK (stock >= 0);
    END IF;

    -- Users
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_user_email_format') THEN
        ALTER TABLE users ADD CONSTRAINT chk_user_email_format CHECK (email ~* '^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_user_role') THEN
        ALTER TABLE users ADD CONSTRAINT chk_user_role CHECK (role IN ('customer', 'admin', 'manager'));
    END IF;

    -- Reviews
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_review_rating') THEN
        ALTER TABLE reviews ADD CONSTRAINT chk_review_rating CHECK (rating BETWEEN 1 AND 5);
    END IF;

    -- Orders
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_order_status') THEN
        ALTER TABLE orders ADD CONSTRAINT chk_order_status CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_order_total') THEN
        ALTER TABLE orders ADD CONSTRAINT chk_order_total CHECK (total_amount >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_order_payment_status') THEN
        -- Aligned vocabulary: paid, failed, refunded (pending is default)
        ALTER TABLE orders ADD CONSTRAINT chk_order_payment_status CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded'));
    END IF;

    -- Order Items
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_orderitem_quantity') THEN
        ALTER TABLE order_items ADD CONSTRAINT chk_orderitem_quantity CHECK (quantity > 0);
    END IF;

    -- Payments
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_payment_status') THEN
        ALTER TABLE payments ADD CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'paid', 'failed', 'refunded'));
    END IF;

END $$;
