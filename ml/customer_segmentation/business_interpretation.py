"""
business_interpretation.py
---------------------------
Translates numeric cluster IDs into actionable business segment labels.
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np
from .config import Config, cfg

logger = logging.getLogger(__name__)

DEFAULT_SEGMENT_MAP: Dict[int, Dict[str, str]] = {
    0: {"label": "VIP Customers", "emoji": "💎", "strategy": "Exclusive concierge service."},
    1: {"label": "Loyal Buyers", "emoji": "💛", "strategy": "Loyalty program rewards."},
    2: {"label": "Cart Abandoners", "emoji": "🛒", "strategy": "Dynamic retargeting."},
    3: {"label": "Window Shoppers", "emoji": "👀", "strategy": "Personalized recommendations."},
    4: {"label": "Inactive Customers", "emoji": "💤", "strategy": "Win-back discounts."},
    5: {"label": "Wishlist-Driven Users", "emoji": "📜", "strategy": "Price drop alerts."},
    6: {"label": "Regular Customers", "emoji": "📦", "strategy": "Cross-sell relevant categories."},
    7: {"label": "Potential Loyalists", "emoji": "📈", "strategy": "Welcome series."},
    -1: {"label": "Outliers/Noise", "emoji": "🚨", "strategy": "Manual review."},
}

def auto_assign_segments(profile: pd.DataFrame) -> Dict[int, Dict[str, str]]:
    """Assign business labels based on actual feature thresholds (Behavioral heuristics)."""
    if profile.empty:
        return {-1: DEFAULT_SEGMENT_MAP[-1]}

    mapping = {}
    for cid, row in profile.iterrows():
        cid = int(str(cid))  # type conversion via str to satisfy strict type checkers
        if cid == -1:
            mapping[-1] = DEFAULT_SEGMENT_MAP[-1]
            continue
            
        # Decision heuristics
        if row.get("recency_days", 0) > profile.get("recency_days", pd.Series([90])).median() * 1.5:
            # High recency -> Inactive
            mapping[cid] = DEFAULT_SEGMENT_MAP[4]
        elif row.get("total_spent", 0) >= profile.get("total_spent", pd.Series([0])).quantile(0.60):
            # High spend -> VIP
            mapping[cid] = DEFAULT_SEGMENT_MAP[0]
        elif row.get("cart_to_click_ratio", 0) > profile.get("cart_to_click_ratio", pd.Series([0])).median() and row.get("total_orders", 1) < profile.get("total_orders", pd.Series([1])).median():
            # High cart activity but low orders -> Cart Abandoners
            mapping[cid] = DEFAULT_SEGMENT_MAP[2]
        elif row.get("total_orders", 0) >= profile.get("total_orders", pd.Series([0])).median():
            # Solid order count -> Loyal Buyers
            mapping[cid] = DEFAULT_SEGMENT_MAP[1]
        elif row.get("views_count", 0) > profile.get("views_count", pd.Series([0])).median() and row.get("total_orders", 1) <= profile.get("total_orders", pd.Series([1])).quantile(0.25):
            # High views but low/no orders -> Window Shoppers
            mapping[cid] = DEFAULT_SEGMENT_MAP[3]
        else:
            # Fallback -> Regular Customers
            mapping[cid] = DEFAULT_SEGMENT_MAP[6]
            
    return mapping

def interpret_and_save(df_raw: pd.DataFrame, df_clean: pd.DataFrame, labels: np.ndarray, 
                       feature_cols: list, config: Config = cfg) -> pd.DataFrame:
    """
    Map clusters to business labels and save the final CSV.
    """
    logger.info("=== Business Interpretation ===")
    
    # 1. Join labels to the cleaned data
    df_results = df_clean.copy()
    # List conversion is the safest for strict type checkers
    df_results["cluster"] = [int(x) for x in labels]
    
    # 2. Get cluster profiles from raw data
    # Ensure indices match or use user_id mapping
    df_raw_joined = df_raw[df_raw["user_id"].isin(df_clean["user_id"])].copy()
    id_to_cluster = dict(zip(df_clean["user_id"].tolist(), [int(x) for x in labels]))
    df_raw_joined["cluster"] = df_raw_joined["user_id"].map(id_to_cluster).fillna(-1).astype(int)
    
    profile = df_raw_joined.groupby("cluster")[feature_cols].mean()
    segment_map = auto_assign_segments(profile)
    
    # 3. Apply labels
    # Force cast to Series to ensure the IDE recognizes the .map method
    cluster_series = pd.Series(df_results["cluster"])
    df_results["segment"] = cluster_series.map(lambda c: segment_map.get(int(c), {}).get("label", f"Cluster {c}"))
    df_results["emoji"] = cluster_series.map(lambda c: segment_map.get(int(c), {}).get("emoji", "📦"))
    df_results["strategy"] = cluster_series.map(lambda c: segment_map.get(int(c), {}).get("strategy", "TBD"))
    
    # 4. Save final labelled users
    out_path = config.data_dir / "best_model_users_labelled.csv"
    df_results.to_csv(out_path, index=False)
    logger.info("Final labelled users saved → %s", out_path)
    
    return df_results
