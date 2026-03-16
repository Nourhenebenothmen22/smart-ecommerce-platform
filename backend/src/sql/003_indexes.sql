-- ==========================================
-- INDEX RECOMMANDÉS (Performances)
-- ==========================================
-- Sur environnement e-commerce avec des millions de traces, un index sur Clés étrangères est INDISPENSABLE.
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_subcategory ON products(subcategory_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_interactions_user ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_product ON user_interactions(product_id);

-- Quelques Index cibles pour la rapidité des recherches ou statuts
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_generic ON audit_logs(entity_type, entity_id);

-- Index Vectoriel (Permet de faire du text2image ou text2product text match ultra efficace)
-- (S'assure que pgevector extension est chargée)
CREATE INDEX IF NOT EXISTS idx_product_embeddings_vec ON product_embeddings USING hnsw (embedding_vector vector_cosine_ops);
