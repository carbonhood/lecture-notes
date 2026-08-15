"""Shared end-to-end pipeline helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from lecture_notes.config import Config
from lecture_notes.structure import structure_from_result, structure_notes
from lecture_notes.transcribe import TranscriptResult, transcribe_audio
from lecture_notes.vault import save_to_vault

logger = logging.getLogger(__name__)


def resolve_whisper_model(config: Config, draft: bool = False) -> str:
    """Return draft or final Whisper model size from config."""
    if draft:
        return config.whisper_draft_model or "base"
    return config.whisper_model or "small"


def process_audio_file(
    audio_path: Path,
    config: Config,
    subject: str = "General",
    lecture_name: str | None = None,
    date: str | None = None,
    *,
    draft: bool = False,
    language: str | None = None,
) -> Path:
    """Run transcribe → structure → vault for one audio file."""
    name = lecture_name or audio_path.stem
    model_size = resolve_whisper_model(config, draft=draft)
    lang = language if language is not None else config.whisper_language

    logger.info(
        "Processing %s as '%s' (model=%s, draft=%s)",
        audio_path,
        name,
        model_size,
        draft,
    )
    result = transcribe_audio(
        audio_path,
        model_size=model_size,
        language=lang,
        preprocess=config.ffmpeg_preprocess,
    )
    notes = structure_from_result(
        result,
        subject=subject,
        llm_model=config.llm_model,
        chunk_seconds=config.chunk_seconds,
    )
    return save_to_vault(
        notes,
        name,
        config,
        subject=subject,
        date=date,
        source_audio=audio_path.resolve(),
        transcript=result.text,
        aliases=[name],
    )


def restructure_transcript_file(
    transcript_path: Path,
    config: Config,
    lecture_name: str,
    subject: str = "General",
    date: str | None = None,
) -> Path:
    """Re-run LLM structuring from a saved transcript without Whisper."""
    try:
        raw = transcript_path.read_text(encoding="utf-8")
    except OSError as exc:
        from lecture_notes.errors import VaultWriteError

        raise VaultWriteError(
            f"Could not read transcript file {transcript_path}: {exc}"
        ) from exc

    # Drop YAML frontmatter if present
    text = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]

    notes = structure_notes(
        text.strip(),
        subject=subject,
        llm_model=config.llm_model,
        chunk_seconds=config.chunk_seconds,
    )
    return save_to_vault(
        notes,
        lecture_name,
        config,
        subject=subject,
        date=date,
        transcript=text.strip() if config.save_transcript else None,
        aliases=[lecture_name],
    )


def transcribe_only(
    audio_path: Path,
    config: Config,
    *,
    draft: bool = False,
    language: str | None = None,
) -> TranscriptResult:
    """Transcribe without structuring (used by serve progress steps)."""
    model_size = resolve_whisper_model(config, draft=draft)
    lang = language if language is not None else config.whisper_language
    return transcribe_audio(
        audio_path,
        model_size=model_size,
        language=lang,
        preprocess=config.ffmpeg_preprocess,
    )
