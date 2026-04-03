-- ==========================================
-- ANALYTICAL VIEW FOR USER SEGMENTATION
-- ==========================================

CREATE OR REPLACE VIEW v_user_behavior_features AS
WITH 

-- 1. Aggregating Order Data
order_agg AS (
    SELECT 
        user_id,
        COUNT(id) AS total_orders,
        COALESCE(SUM(total_amount), 0) AS total_spent,
        COALESCE(AVG(total_amount), 0) AS avg_order_value,
        MAX(created_at) AS last_order_at
    FROM orders
    GROUP BY user_id
),

-- 2. Aggregating Order Items (separately to avoid double counting orders)
items_agg AS (
    SELECT 
        o.user_id,
        SUM(oi.quantity) AS total_items_bought
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    GROUP BY o.user_id
),

-- 3. Aggregating Reviews
review_agg AS (
    SELECT 
        user_id,
        COUNT(id) AS reviews_count,
        COALESCE(AVG(rating), 0) AS avg_rating_given
    FROM reviews
    GROUP BY user_id
),

-- 4. Aggregating Wishlist
wishlist_agg AS (
    SELECT 
        user_id,
        COUNT(id) AS wishlist_count
    FROM wishlists
    GROUP BY user_id
),

-- 5. Aggregating Cart Items
cart_agg AS (
    SELECT 
        user_id,
        COUNT(id) AS cart_count
    FROM cart_items
    GROUP BY user_id
),

-- 6. Aggregating Interactions (Pivoted)
interaction_agg AS (
    SELECT 
        user_id,
        COUNT(*) FILTER (WHERE interaction_type = 'view') AS views_count,
        COUNT(*) FILTER (WHERE interaction_type = 'click') AS clicks_count,
        COUNT(*) FILTER (WHERE interaction_type = 'add_to_cart')      AS cart_add_count,
        COUNT(*) FILTER (WHERE interaction_type = 'add_to_wishlist') AS wishlist_add_count,
        COUNT(*) FILTER (WHERE interaction_type = 'purchase') AS purchase_interaction_count,
        COUNT(*) FILTER (WHERE interaction_type = 'search') AS search_count,
        COUNT(*) FILTER (WHERE interaction_type = 'share') AS share_count,
        MAX(created_at) AS last_interaction_at
    FROM user_interactions
    GROUP BY user_id
)

-- Final Join
SELECT 
    u.id AS user_id,
    u.created_at AS user_created_at,
    COALESCE(oa.total_orders, 0) AS total_orders,
    COALESCE(oa.total_spent, 0) AS total_spent,
    COALESCE(oa.avg_order_value, 0) AS avg_order_value,
    COALESCE(ia_items.total_items_bought, 0) AS total_items_bought,
    COALESCE(ra.reviews_count, 0) AS reviews_count,
    COALESCE(ra.avg_rating_given, 0) AS avg_rating_given,
    COALESCE(wa.wishlist_count, 0) AS wishlist_count,
    COALESCE(ca.cart_count, 0) AS cart_count,
    COALESCE(ia.views_count, 0) AS views_count,
    COALESCE(ia.clicks_count, 0) AS clicks_count,
    COALESCE(ia.cart_add_count, 0) AS cart_add_count,
    COALESCE(ia.wishlist_add_count, 0) AS wishlist_add_count,
    COALESCE(ia.purchase_interaction_count, 0) AS purchase_interaction_count,
    COALESCE(ia.search_count, 0) AS search_count,
    COALESCE(ia.share_count, 0) AS share_count,
    oa.last_order_at,
    ia.last_interaction_at
FROM users u
LEFT JOIN order_agg oa ON u.id = oa.user_id
LEFT JOIN items_agg ia_items ON u.id = ia_items.user_id
LEFT JOIN review_agg ra ON u.id = ra.user_id
LEFT JOIN wishlist_agg wa ON u.id = wa.user_id
LEFT JOIN cart_agg ca ON u.id = ca.user_id
LEFT JOIN interaction_agg ia ON u.id = ia.user_id;
