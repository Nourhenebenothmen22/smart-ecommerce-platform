-- ==========================================
-- VERIFICATION SCRIPT: SCHEMA INTEGRITY
-- ==========================================

-- 1. Verify Nullability
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'products' AND column_name IN ('category_id', 'subcategory_id');

SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'orders' AND column_name = 'user_id';

-- 2. Verify Category/Subcategory FK (Negative Test)
-- This SHOULD FAIL if you run it (subcategory 999 doesn't exist or isn't in category 1)
-- INSERT INTO products (title, slug, description, brand, category_id, subcategory_id, price, thumbnail)
-- VALUES ('Test Product', 'test-product', 'Desc', 'Brand', 1, 999, 100, 'thumb.jpg');

-- 3. Verify Triggers (Aggregate Maintenance)
-- A. Insert a test product and review
-- INSERT INTO categories (name, slug) VALUES ('Test Cat', 'test-cat') ON CONFLICT DO NOTHING;
-- INSERT INTO subcategories (category_id, name, slug) VALUES (1, 'Test Sub', 'test-sub') ON CONFLICT DO NOTHING;
-- INSERT INTO products (id, title, slug, description, brand, category_id, subcategory_id, price, thumbnail) 
-- VALUES (9999, 'Trigger Test', 'trigger-test', 'Desc', 'Brand', 1, 1, 100, 'thumb.jpg');

-- INSERT INTO reviews (product_id, rating, review_text) VALUES (9999, 5, 'Great!');
-- INSERT INTO reviews (product_id, rating, review_text) VALUES (9999, 1, 'Bad!');

-- SELECT rating_avg, review_count FROM products WHERE id = 9999;
-- Expected: rating_avg = 3.0, review_count = 2

-- B. Test Order Total
-- INSERT INTO orders (id, user_id) VALUES (9999, 1);
-- INSERT INTO order_items (order_id, product_id, product_name_snapshot, quantity, unit_price, subtotal)
-- VALUES (9999, 9999, 'Trigger Test', 2, 100, 200);

-- SELECT total_amount FROM orders WHERE id = 9999;
-- Expected: total_amount = 200

-- 4. Verify Index De-duplication
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'orders' AND indexname LIKE 'idx_orders_user%';
-- Should only show idx_orders_user
