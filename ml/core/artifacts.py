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


def _remove_path(path: Path, ignore_errors: bool = False) -> None:
    try:
        if path.is_dir():
            _remove_tree(path, ignore_errors=ignore_errors)
            return
        try:
            os.chmod(path, stat.S_IWRITE)
        except OSError:
            pass
        path.unlink()
    except FileNotFoundError:
        return
    except Exception:
        if not ignore_errors:
            raise


def _sync_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    source_names = {child.name for child in source.iterdir()}
    for child in list(target.iterdir()):
        if child.name not in source_names:
            _remove_path(child)

    for child in source.iterdir():
        destination = target / child.name
        if child.is_dir():
            _sync_tree(child, destination)
        else:
            shutil.copy2(child, destination)


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

    replacement = final.with_name(f".{final.name}.replacement-{uuid.uuid4().hex}")
    previous = final.with_name(f".{final.name}.previous-{uuid.uuid4().hex}")
    if replacement.exists():
        _remove_tree(replacement)
    if previous.exists():
        _remove_tree(previous)

    published = False
    try:
        shutil.copytree(staging, replacement)
        _remove_tree(staging, ignore_errors=True)
        if final.exists():
            shutil.copytree(final, previous)

        try:
            _sync_tree(replacement, final)
            published = True
        except Exception:
            if previous.exists():
                _sync_tree(previous, final)
            raise
    finally:
        if replacement.exists():
            _remove_tree(replacement, ignore_errors=True)
        if previous.exists() and published:
            _remove_tree(previous, ignore_errors=True)
        apply_artifact_layout(config, final)
        cleanup_empty_staging(final.parent)


def discard_staged_artifact(config, run: ArtifactRun) -> None:
    if run.staging_root.exists():
        _remove_tree(run.staging_root, ignore_errors=True)
    apply_artifact_layout(config, run.final_root)


def cleanup_empty_staging(root: Path) -> None:
    staging = root / ".staging"
    if staging.exists() and not any(staging.iterdir()):
        staging.rmdir()
