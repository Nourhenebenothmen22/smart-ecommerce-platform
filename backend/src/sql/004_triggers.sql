-- ==========================================
-- TRIGGERS & FUNCTIONS (IDEMPOTENT)
-- ==========================================

-- 1. Generic Updated At
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_products_updated ON products;
CREATE TRIGGER trg_products_updated BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_users_updated ON users;
CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_cart_updated ON cart_items;
CREATE TRIGGER trg_cart_updated BEFORE UPDATE ON cart_items FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_orders_updated ON orders;
CREATE TRIGGER trg_orders_updated BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 2. Maintain Order Total Amount
CREATE OR REPLACE FUNCTION maintain_order_total()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
        UPDATE orders 
        SET total_amount = (SELECT COALESCE(SUM(subtotal), 0) FROM order_items WHERE order_id = NEW.order_id)
        WHERE id = NEW.order_id;
    END IF;
    IF (TG_OP = 'DELETE') THEN
        UPDATE orders 
        SET total_amount = (SELECT COALESCE(SUM(subtotal), 0) FROM order_items WHERE order_id = OLD.order_id)
        WHERE id = OLD.order_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_maintain_order_total ON order_items;
CREATE TRIGGER trg_maintain_order_total AFTER INSERT OR UPDATE OR DELETE ON order_items FOR EACH ROW EXECUTE FUNCTION maintain_order_total();

-- 3. Maintain Product Review Stats
CREATE OR REPLACE FUNCTION maintain_product_review_stats()
RETURNS TRIGGER AS $$
DECLARE
    target_product_id INTEGER;
BEGIN
    IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
        target_product_id := NEW.product_id;
    ELSE
        target_product_id := OLD.product_id;
    END IF;

    UPDATE products
    SET 
        rating_avg = (SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE product_id = target_product_id),
        review_count = (SELECT COUNT(*) FROM reviews WHERE product_id = target_product_id)
    WHERE id = target_product_id;

    RETURN NULL;   
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_maintain_product_review_stats ON reviews;
CREATE TRIGGER trg_maintain_product_review_stats AFTER INSERT OR UPDATE OR DELETE ON reviews FOR EACH ROW EXECUTE FUNCTION maintain_product_review_stats();
