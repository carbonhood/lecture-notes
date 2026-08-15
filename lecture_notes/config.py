"""Configuration loading with defaults and optional YAML overrides."""

from __future__ import annotations

import logging
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = "config.yaml"


@dataclass
class Config:
    """Runtime configuration for transcription, structuring, and vault output."""

    vault_path: Path = Path("~/Obsidian Vault")
    lectures_folder: str = "Lectures"
    watch_folder: Path = Path("~/LectureRecordings")
    whisper_model: str = "small"
    whisper_draft_model: str = "base"
    whisper_language: str = "en"
    llm_model: str = "mistral"
    chunk_seconds: int = 600
    save_transcript: bool = True
    ffmpeg_preprocess: bool = True
    moc_note: str = "Lectures MOC"
    serve_host: str = "0.0.0.0"
    serve_port: int = 8787


def _expand_path(value: Path | str) -> Path:
    return Path(value).expanduser().resolve()


def _apply_overrides(data: dict[str, Any]) -> Config:
    known = {f.name for f in fields(Config)}
    kwargs: dict[str, Any] = {}
    for key, value in data.items():
        if key not in known:
            logger.warning("Ignoring unknown config key: %s", key)
            continue
        kwargs[key] = value
    cfg = Config(**kwargs)
    cfg.vault_path = _expand_path(cfg.vault_path)
    cfg.watch_folder = _expand_path(cfg.watch_folder)
    return cfg


def load_config(path: Path | None = None) -> Config:
    """Load config from YAML if present; otherwise return expanded defaults.

    Looks for ``config.yaml`` in the current working directory when ``path``
    is not provided.
    """
    config_path = path if path is not None else Path.cwd() / DEFAULT_CONFIG_NAME
    if not config_path.is_file():
        logger.info("No config file at %s; using defaults", config_path)
        return _apply_overrides({})

    try:
        with config_path.open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
    except OSError as exc:
        raise OSError(f"Could not read config file {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"Config file {config_path} must contain a YAML mapping")

    logger.info("Loaded config from %s", config_path)
    return _apply_overrides(raw)
