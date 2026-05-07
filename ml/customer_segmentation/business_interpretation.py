"""
business_interpretation.py
---------------------------
Translates numeric cluster IDs into actionable business segment labels,
builds enriched user profiles and exports a business-ready report.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .config import Config, cfg

logger = logging.getLogger(__name__)


# ─── Default Segment Taxonomy ─────────────────────────────────────────────────
# Keys are cluster IDs (int), values are dicts with label and strategy.
# Override this mapping after inspecting cluster profiles.

DEFAULT_SEGMENT_MAP = {
    0: {
        "label":    "VIP Customers",
        "emoji":    "💎",
        "description": "High value, frequent orders, and recent activity.",
        "strategy": "Exclusive concierge service and early access.",
    },
    1: {
        "label":    "Loyal Buyers",
        "emoji":    "💛",
        "description": "Regular purchases and consistent engagement.",
        "strategy": "Loyalty program points and milestone rewards.",
    },
    2: {
        "label":    "Cart Abandoners",
        "emoji":    "🛒",
        "description": "High interaction with cart but low conversion.",
        "strategy": "Dynamic retargeting and limited-time coupons.",
    },
    3: {
        "label":    "Window Shoppers",
        "emoji":    "👀",
        "description": "High view count but rare purchases.",
        "strategy": "Personalised product recommendations based on views.",
    },
    4: {
        "label":    "Inactive Customers",
        "emoji":    "💤",
        "description": "No orders or interactions for a long time.",
        "strategy": "Win-back emails and deep reactivation discounts.",
    },
    5: {
        "label":    "Wishlist-Driven Users",
        "emoji":    "📜",
        "description": "High wishlist additions, waiting for price drops.",
        "strategy": "Alerts on wishlist items and price drop notifications.",
    },
    6: {
        "label":    "Regular Customers",
        "emoji":    "📦",
        "description": "Standard behavior, consistent but not highly active.",
        "strategy": "Cross-sell relevant categories.",
    },
    7: {
        "label":    "Potential Loyalists",
        "emoji":    "📈",
        "description": "Newer users with high initial engagement.",
        "strategy": "Welcome series and second-purchase incentives.",
    },
    -1: {
        "label":    "Outliers",
        "emoji":    "🚨",
        "description": "Unusual behavior (bot-like or extreme bulk buyers).",
        "strategy": "Manual review or fraud check.",
    },
}


# ─── Labelling ────────────────────────────────────────────────────────────────

def auto_assign_segments(profile: pd.DataFrame,
                         feature_cols: list[str] | None = None) -> dict[int, str]:
    """
    Heuristically rank clusters by composite score:
      high total_spent + high total_orders + low recency_days → best segment.

    Returns
    -------
    dict mapping cluster_id → segment rank (0 = best)
    """
    if feature_cols is None:
        feature_cols = ["total_spent", "total_orders", "recency_days"]

    score = pd.Series(0.0, index=profile.index)
    if "total_spent" in profile.columns:
        score += profile["total_spent"].rank(pct=True)
    if "total_orders" in profile.columns:
        score += profile["total_orders"].rank(pct=True)
    if "recency_days" in profile.columns:
        score -= profile["recency_days"].rank(pct=True)  # lower recency = better

    ranked = score.sort_values(ascending=False)
    return {cluster: rank for rank, cluster in enumerate(ranked.index)}


def label_dataframe(df_with_cluster: pd.DataFrame, cluster_col: str,
                    segment_map: dict | None = None) -> pd.DataFrame:
    """
    Add 'segment_label', 'segment_emoji', 'segment_strategy' columns to df.

    Parameters
    ----------
    df_with_cluster : DataFrame with a cluster ID column
    cluster_col     : name of the cluster column (e.g. 'kmeans_cluster')
    segment_map     : dict mapping cluster_id → segment info (uses DEFAULT if None)
    """
    if segment_map is None:
        segment_map = DEFAULT_SEGMENT_MAP

    df = df_with_cluster.copy()
    df["segment_label"]    = df[cluster_col].map(lambda c: segment_map.get(c, {}).get("label",    f"Segment {c}"))
    df["segment_emoji"]    = df[cluster_col].map(lambda c: segment_map.get(c, {}).get("emoji",    "❓"))
    df["segment_strategy"] = df[cluster_col].map(lambda c: segment_map.get(c, {}).get("strategy", "TBD"))
    return df


# ─── Reporting ────────────────────────────────────────────────────────────────

def build_segment_report(df_labelled: pd.DataFrame, cluster_col: str,
                         feature_cols: list[str], config: Config = cfg,
                         model_name: str = "Model") -> pd.DataFrame:
    """
    Aggregate statistics per segment and export a CSV + formatted text report.
    """
    agg = df_labelled.groupby(["segment_label", cluster_col]).agg(
        user_count     =(cluster_col, "count"),
        **{f: (f, "mean") for f in feature_cols if f in df_labelled.columns},
    ).round(2).reset_index()

    agg["user_pct"] = (agg["user_count"] / agg["user_count"].sum() * 100).round(1)

    csv_path = config.reports_dir / "best_model_segment_report.csv"
    agg.to_csv(csv_path, index=False)
    logger.info("Segment report CSV → %s", csv_path)

    # Text report
    txt_path = config.reports_dir / f"{model_name.lower()}_segment_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"=== {model_name} -- Business Segment Report ===\n\n")
        for _, row in agg.iterrows():
            # Get data from the row (which was grouped by label and cluster_id)
            label = row["segment_label"]
            cluster_id = int(row[cluster_col])
            
            # Find an example row in the original df to get the emoji/strategy
            sample = df_labelled[df_labelled[cluster_col] == cluster_id].iloc[0]
            emoji = sample.get("segment_emoji", "📦")
            strategy = sample.get("segment_strategy", "TBD")

            f.write(f"{'─'*60}\n")
            f.write(f"Segment : {emoji}{label} (ID: {cluster_id})\n")
            f.write(f"Users   : {int(row['user_count'])} ({row['user_pct']}%)\n")
            f.write(f"Strategy: {strategy}\n")
            for feat in feature_cols:
                if feat in row:
                    f.write(f"  {feat:<30} {row[feat]:.2f}\n")
            f.write("\n")
    logger.info("Segment report TXT → %s", txt_path)
    return agg


# ─── Visualisations ───────────────────────────────────────────────────────────




# ─── Full Run ─────────────────────────────────────────────────────────────────

def interpret(df_raw: pd.DataFrame, df_clean: pd.DataFrame, labels: np.ndarray,
              cluster_col: str, feature_cols: list[str],
              profile: pd.DataFrame | None = None, config: Config = cfg,
              model_name: str = "Model") -> pd.DataFrame:
    """
    Full interpretation pipeline.
    Uses df_raw for profiling (real values) and labels from df_clean.
    """
    logger.info("=== Business Interpretation -- %s ===", model_name)

    # 1. Join labels to raw data for profiling
    df_labelled = df_raw.copy()
    # Ensure users survived preprocessing
    df_labelled = df_labelled[df_labelled["user_id"].isin(df_clean["user_id"])].copy()
    
    id_to_label = dict(zip(df_clean["user_id"], labels))
    df_labelled[cluster_col] = df_labelled["user_id"].map(id_to_label)

    # 2. Auto-rank clusters using RAW data profile
    raw_profile = df_labelled.groupby(cluster_col).agg({f: "mean" for f in feature_cols if f in df_labelled.columns})
    rank_map = auto_assign_segments(raw_profile, feature_cols)

    # 3. Build segment map
    default_keys = list(range(8)) # Support up to 8 segments
    segment_map = {}
    for cluster_id, rank in rank_map.items():
        if cluster_id == -1:
            segment_map[-1] = DEFAULT_SEGMENT_MAP[-1]
        else:
            key = default_keys[rank] if rank < len(default_keys) else rank
            segment_map[cluster_id] = DEFAULT_SEGMENT_MAP.get(key, {
                "label": f"Segment {cluster_id}", "emoji": "📦",
                "description": "", "strategy": "TBD",
            })

    # Apply labels
    df_labelled = label_dataframe(df_labelled, cluster_col, segment_map)

    out_path = config.data_dir / "best_model_users_labelled.csv"
    df_labelled.to_csv(out_path, index=False)
    logger.info("Labelled users saved → %s", out_path)

    return df_labelled
