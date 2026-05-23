"""
Persistence helpers for customer segmentation model metadata and assignments.
"""

import json
from typing import Any

import pandas as pd

from ml.core.db import get_db_cursor

from .config import Config, cfg


def register_segmentation_model(
    algorithm: str,
    metrics: dict[str, Any],
    artifact_path: str,
    config: Config = cfg,
) -> None:
    """Upsert the active segmentation model metadata used by user_segments."""
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO ml_models (model_name, model_version, model_type, metrics, artifact_path, is_active)
            VALUES (%s, %s, %s, %s::jsonb, %s, true)
            ON CONFLICT (model_name, model_version)
            DO UPDATE SET
                model_type = EXCLUDED.model_type,
                metrics = EXCLUDED.metrics,
                artifact_path = EXCLUDED.artifact_path,
                is_active = true,
                trained_at = NOW()
            """,
            (
                config.segmentation_model_name,
                config.segmentation_model_version,
                algorithm,
                json.dumps(metrics),
                artifact_path,
            ),
        )


def persist_user_segments(df_labelled: pd.DataFrame, config: Config = cfg) -> int:
    """
    Upsert user segment assignments produced by the segmentation pipeline.
    """
    required = {"user_id", "cluster", "segment"}
    missing = required - set(df_labelled.columns)
    if missing:
        raise ValueError(f"Cannot persist user_segments; missing columns: {sorted(missing)}")

    rows = [
        (
            int(row.user_id),
            int(row.cluster),
            str(row.segment),
            config.segmentation_model_name,
            config.segmentation_model_version,
        )
        for row in df_labelled.itertuples(index=False)
    ]

    if not rows:
        return 0

    with get_db_cursor(commit=True) as cur:
        cur.executemany(
            """
            INSERT INTO user_segments (
                user_id, segment_id, segment_label, model_name, model_version, assigned_at
            )
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, model_name, model_version)
            DO UPDATE SET
                segment_id = EXCLUDED.segment_id,
                segment_label = EXCLUDED.segment_label,
                assigned_at = NOW()
            """,
            rows,
        )

    return len(rows)
