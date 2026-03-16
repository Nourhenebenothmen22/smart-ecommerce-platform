-- ==========================================
-- CONTRANTES : FOREIGN KEYS
-- ==========================================
ALTER TABLE subcategories ADD CONSTRAINT fk_subcat_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;

ALTER TABLE products ADD CONSTRAINT fk_prod_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
ALTER TABLE products ADD CONSTRAINT fk_prod_subcategory FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE RESTRICT;

ALTER TABLE reviews ADD CONSTRAINT fk_rev_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE reviews ADD CONSTRAINT fk_rev_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE cart_items ADD CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE cart_items ADD CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;

ALTER TABLE orders ADD CONSTRAINT fk_ord_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;

ALTER TABLE order_items ADD CONSTRAINT fk_orditem_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
ALTER TABLE order_items ADD CONSTRAINT fk_orditem_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;

ALTER TABLE payments ADD CONSTRAINT fk_pay_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT;

ALTER TABLE user_interactions ADD CONSTRAINT fk_uint_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE user_interactions ADD CONSTRAINT fk_uint_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;

ALTER TABLE recommendations ADD CONSTRAINT fk_rec_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE recommendations ADD CONSTRAINT fk_rec_src_product FOREIGN KEY (source_product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE recommendations ADD CONSTRAINT fk_rec_rec_product FOREIGN KEY (recommended_product_id) REFERENCES products(id) ON DELETE CASCADE;

ALTER TABLE review_analysis ADD CONSTRAINT fk_revanal_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE;

ALTER TABLE product_embeddings ADD CONSTRAINT fk_prodembed_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;

ALTER TABLE wishlists ADD CONSTRAINT fk_wish_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE wishlists ADD CONSTRAINT fk_wish_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;

ALTER TABLE voice_confirmations ADD CONSTRAINT fk_voice_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;

ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;


-- ==========================================
-- CONTRAINTES : UNIQUE
-- ==========================================
ALTER TABLE categories ADD CONSTRAINT uq_category_slug UNIQUE (slug);
ALTER TABLE subcategories ADD CONSTRAINT uq_subcategory_slug UNIQUE (slug);
ALTER TABLE products ADD CONSTRAINT uq_product_slug UNIQUE (slug);
ALTER TABLE users ADD CONSTRAINT uq_user_email UNIQUE (email);

ALTER TABLE reviews ADD CONSTRAINT uq_review_user_product UNIQUE (user_id, product_id);
ALTER TABLE cart_items ADD CONSTRAINT uq_cart_user_product UNIQUE (user_id, product_id);
ALTER TABLE order_items ADD CONSTRAINT uq_orderitem_order_product UNIQUE (order_id, product_id);
ALTER TABLE payments ADD CONSTRAINT uq_payment_order UNIQUE (order_id);
ALTER TABLE recommendations ADD CONSTRAINT uq_rec_user_source_rec UNIQUE (user_id, source_product_id, recommended_product_id);
ALTER TABLE review_analysis ADD CONSTRAINT uq_revanal_review UNIQUE (review_id);
ALTER TABLE product_embeddings ADD CONSTRAINT uq_prodembed_product_model UNIQUE (product_id, model_name);
ALTER TABLE wishlists ADD CONSTRAINT uq_wishlst_user_product UNIQUE (user_id, product_id);
ALTER TABLE voice_confirmations ADD CONSTRAINT uq_voice_order UNIQUE (order_id);


-- ==========================================
-- CONTRAINTES : CHECK
-- ==========================================
ALTER TABLE products ADD CONSTRAINT chk_product_price CHECK (price >= 0);
ALTER TABLE products ADD CONSTRAINT chk_product_discount CHECK (discount_percent BETWEEN 0 AND 100);
ALTER TABLE products ADD CONSTRAINT chk_product_rating CHECK (rating_avg BETWEEN 0.00 AND 5.00);
ALTER TABLE products ADD CONSTRAINT chk_product_review_count CHECK (review_count >= 0);
ALTER TABLE products ADD CONSTRAINT chk_product_stock CHECK (stock >= 0);

ALTER TABLE users ADD CONSTRAINT chk_user_email_format CHECK (email ~* '^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$');
ALTER TABLE users ADD CONSTRAINT chk_user_role CHECK (role IN ('customer', 'admin', 'manager'));

ALTER TABLE reviews ADD CONSTRAINT chk_review_rating CHECK (rating BETWEEN 1 AND 5);

ALTER TABLE cart_items ADD CONSTRAINT chk_cart_quantity CHECK (quantity > 0);

ALTER TABLE orders ADD CONSTRAINT chk_order_status CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'));
ALTER TABLE orders ADD CONSTRAINT chk_order_total CHECK (total_amount >= 0);
ALTER TABLE orders ADD CONSTRAINT chk_order_payment_status CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded'));

ALTER TABLE order_items ADD CONSTRAINT chk_orderitem_quantity CHECK (quantity > 0);
ALTER TABLE order_items ADD CONSTRAINT chk_orderitem_unit_price CHECK (unit_price >= 0);
ALTER TABLE order_items ADD CONSTRAINT chk_orderitem_subtotal CHECK (subtotal >= 0);

ALTER TABLE payments ADD CONSTRAINT chk_payment_amount CHECK (amount >= 0);
ALTER TABLE payments ADD CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'completed', 'failed', 'refunded'));

ALTER TABLE recommendations ADD CONSTRAINT chk_rec_score CHECK (score >= 0);

ALTER TABLE review_analysis ADD CONSTRAINT chk_revanal_sentiment CHECK (sentiment_label IN ('positive', 'neutral', 'negative'));
ALTER TABLE review_analysis ADD CONSTRAINT chk_revanal_score CHECK (sentiment_score BETWEEN -1.0 AND 1.0);

ALTER TABLE voice_confirmations ADD CONSTRAINT chk_voice_status CHECK (call_status IN ('pending', 'completed', 'failed', 'ignored'));
