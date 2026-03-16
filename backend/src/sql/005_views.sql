CREATE OR REPLACE VIEW product_review_summary AS
SELECT
    p.id AS product_id,
    p.title,
    p.rating_avg,
    p.review_count,
    COUNT(r.id) AS total_reviews
FROM products p
LEFT JOIN reviews r ON r.product_id = p.id
GROUP BY p.id, p.title, p.rating_avg, p.review_count;

CREATE OR REPLACE VIEW order_summary AS
SELECT
    o.id AS order_id,
    o.user_id,
    o.status,
    o.payment_status,
    o.total_amount,
    COUNT(oi.id) AS total_items
FROM orders o
LEFT JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id, o.user_id, o.status, o.payment_status, o.total_amount;