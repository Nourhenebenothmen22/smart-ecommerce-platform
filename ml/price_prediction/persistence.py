"""
Persistence helpers for price prediction model metadata.
"""

import json
from typing import Any

from ml.core.db import get_db_cursor

from .config import Config, cfg


def register_price_prediction_model(
    algorithm: str,
    metrics: dict[str, Any],
    parameters: dict[str, Any],
    artifact_path: str,
    config: Config = cfg,
) -> None:
    """Upsert active price prediction model metadata into ml_models."""
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO ml_models (
                model_name, model_version, model_type, algorithm, metrics,
                parameters, artifact_path, is_active, trained_at
            )
            VALUES (%s, %s, 'price_prediction', %s, %s::jsonb, %s::jsonb, %s, true, NOW())
            ON CONFLICT (model_name, model_version)
            DO UPDATE SET
                model_type = EXCLUDED.model_type,
                algorithm = EXCLUDED.algorithm,
                metrics = EXCLUDED.metrics,
                parameters = EXCLUDED.parameters,
                artifact_path = EXCLUDED.artifact_path,
                is_active = true,
                trained_at = NOW()
            """,
            (
                config.price_model_name,
                config.price_model_version,
                algorithm,
                json.dumps(metrics),
                json.dumps(parameters),
                artifact_path,
            ),
        )

