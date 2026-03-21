-- ==========================================
-- INDEX RECOMMANDÉS (Performances)
-- ==========================================

-- Clés étrangères (IDEMPOTENT)
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_subcategory_id ON products(subcategory_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_product_id ON user_interactions(product_id);
CREATE INDEX IF NOT EXISTS idx_wishlists_user_id ON wishlists(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id);

-- Rapidité des recherches ou statuts
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
-- NOTE: idx_users_email est supprimé car uq_user_email (UNIQUE) crée déjà un index.
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_generic ON audit_logs(entity_type, entity_id);

-- Index Vectoriel
CREATE INDEX IF NOT EXISTS idx_product_embeddings_vec ON product_embeddings USING hnsw (embedding_vector vector_cosine_ops);
