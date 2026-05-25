"""
Latest-valid artifact management for ML training runs.

Training writes into a temporary staging folder first. The previous artifact is
replaced only after all expected files are generated and validated.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import stat
import time
import uuid


@dataclass
class ArtifactRun:
    final_root: Path
    staging_root: Path


def ensure_artifact_layout(root: Path) -> None:
    for relative in [
        "model",
        "plots",
        "reports",
        "data/raw",
        "data/processed",
        "metadata",
    ]:
        (root / relative).mkdir(parents=True, exist_ok=True)


def _remove_tree(path: Path, ignore_errors: bool = False) -> None:
    def _make_writable_and_retry(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:
            if not ignore_errors:
                raise

    for attempt in range(5):
        try:
            shutil.rmtree(path, ignore_errors=ignore_errors, onexc=_make_writable_and_retry)
            return
        except PermissionError:
            if attempt == 4:
                if ignore_errors:
                    return
                raise
            time.sleep(0.25)


def apply_artifact_layout(config, root: Path) -> None:
    config.artifacts_dir = root
    config.models_dir = root / "model"
    config.plots_dir = root / "plots"
    config.reports_dir = root / "reports"
    config.data_dir = root / "data"
    config.raw_data_dir = root / "data" / "raw"
    config.processed_data_dir = root / "data" / "processed"
    config.metadata_dir = root / "metadata"
    ensure_artifact_layout(root)


def begin_latest_artifact_run(config, final_root: Path | None = None) -> tuple[ArtifactRun, object]:
    """Start a new artifact run using a *deep copy* of the configuration.

    Returns (ArtifactRun, local_config) where local_config is an isolated copy
    whose path attributes point to the staging directory.  The original global
    ``config`` is **never** mutated, so live inference endpoints keep working
    while a training pipeline runs.
    """
    import copy

    final = Path(final_root or config.artifacts_dir).resolve()
    staging_parent = final.parent / ".staging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = staging_parent / f"{final.name}_{uuid.uuid4().hex}"
    ensure_artifact_layout(staging)

    local_config = copy.deepcopy(config)
    apply_artifact_layout(local_config, staging)

    return ArtifactRun(final_root=final, staging_root=staging), local_config


def validate_artifact_files(root: Path, required_files: list[str]) -> None:
    ensure_artifact_layout(root)
    missing = []
    empty = []
    for relative in required_files:
        path = root / relative
        if not path.exists():
            missing.append(relative)
        elif path.is_file() and path.stat().st_size == 0:
            empty.append(relative)
    if missing or empty:
        raise ValueError(f"Invalid ML artifact. Missing={missing}; empty={empty}")


def publish_latest_artifact(config, run: ArtifactRun) -> None:
    staging = run.staging_root.resolve()
    final = run.final_root.resolve()
    if not staging.exists():
        raise FileNotFoundError(f"Staged artifact does not exist: {staging}")
    if final in staging.parents or staging in final.parents:
        raise ValueError("Refusing to publish nested ML artifact paths.")

    allowed_top_level = {"model", "plots", "reports", "data", "metadata"}
    if final.exists():
        has_existing_files = any(path.is_file() for path in final.rglob("*"))
        if not has_existing_files:
            shutil.copytree(staging, final, dirs_exist_ok=True)
            _remove_tree(staging, ignore_errors=True)
            apply_artifact_layout(config, final)
            return
        try:
            _remove_tree(final)
        except PermissionError:
            shutil.copytree(staging, final, dirs_exist_ok=True)
            _remove_tree(staging, ignore_errors=True)
            for child in final.iterdir():
                if child.name not in allowed_top_level:
                    if child.is_dir():
                        _remove_tree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
            apply_artifact_layout(config, final)
            return
    try:
        shutil.move(str(staging), str(final))
    except Exception:
        raise
    finally:
        apply_artifact_layout(config, final)


def discard_staged_artifact(config, run: ArtifactRun) -> None:
    if run.staging_root.exists():
        _remove_tree(run.staging_root, ignore_errors=True)
    apply_artifact_layout(config, run.final_root)


def cleanup_empty_staging(root: Path) -> None:
    staging = root / ".staging"
    if staging.exists() and not any(staging.iterdir()):
        staging.rmdir()
