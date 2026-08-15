"""Write structured lecture notes into an Obsidian vault."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from lecture_notes.config import Config
from lecture_notes.errors import VaultWriteError

logger = logging.getLogger(__name__)

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_lecture_name(lecture_name: str) -> str:
    """Make a lecture title safe for use as a filename stem."""
    cleaned = _ILLEGAL_CHARS.sub("_", lecture_name.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._")
    if not cleaned:
        raise VaultWriteError("Lecture name is empty after sanitization.")
    return cleaned


def _ensure_lectures_dir(config: Config) -> Path:
    lectures_dir = Path(config.vault_path) / config.lectures_folder
    try:
        lectures_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise VaultWriteError(
            f"Could not create lectures folder at {lectures_dir}: {exc}. "
            "Check vault_path permissions in config.yaml."
        ) from exc
    return lectures_dir


def save_transcript_sidecar(
    transcript: str,
    note_path: Path,
) -> Path:
    """Write a raw transcript next to the note for later re-structuring."""
    sidecar = note_path.with_suffix(".transcript.md")
    body = (
        "---\n"
        'type: "lecture-transcript"\n'
        f'source_note: "[[{note_path.stem}]]"\n'
        "---\n\n"
        f"{transcript.strip()}\n"
    )
    try:
        sidecar.write_text(body, encoding="utf-8")
    except OSError as exc:
        raise VaultWriteError(
            f"Failed to write transcript sidecar {sidecar}: {exc}"
        ) from exc
    logger.info("Wrote transcript sidecar to %s", sidecar)
    return sidecar


def update_moc(
    config: Config,
    note_path: Path,
    subject: str,
    date_str: str,
) -> Path | None:
    """Append a wikilink to the Map of Content note if ``moc_note`` is set."""
    moc_name = (config.moc_note or "").strip()
    if not moc_name:
        return None

    lectures_dir = _ensure_lectures_dir(config)
    moc_path = lectures_dir / f"{sanitize_lecture_name(moc_name)}.md"
    link_line = f"- {date_str} · {subject} · [[{note_path.stem}]]\n"

    try:
        if not moc_path.is_file():
            moc_path.write_text(
                "---\n"
                'type: "moc"\n'
                'tags: [lecture, moc]\n'
                "---\n\n"
                f"# {moc_name}\n\n"
                "Auto-updated index of lecture notes.\n\n"
                "## Lectures\n\n"
                f"{link_line}",
                encoding="utf-8",
            )
        else:
            existing = moc_path.read_text(encoding="utf-8")
            if f"[[{note_path.stem}]]" in existing:
                return moc_path
            if not existing.endswith("\n"):
                existing += "\n"
            moc_path.write_text(existing + link_line, encoding="utf-8")
    except OSError as exc:
        raise VaultWriteError(f"Failed to update MOC {moc_path}: {exc}") from exc

    logger.info("Updated MOC %s", moc_path)
    return moc_path


def save_to_vault(
    content: str,
    lecture_name: str,
    config: Config,
    subject: str = "",
    date: str | None = None,
    *,
    source_audio: Path | None = None,
    transcript: str | None = None,
    aliases: list[str] | None = None,
) -> Path:
    """Write markdown notes with YAML frontmatter into the Obsidian vault.

    Filename format: ``{date}_{sanitized_lecture_name}.md``. Optionally writes
    a ``.transcript.md`` sidecar and appends a link to the configured MOC note.
    """
    now = datetime.now()
    date_str = date or now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    safe_name = sanitize_lecture_name(lecture_name)
    filename = f"{date_str}_{safe_name}.md"

    lectures_dir = _ensure_lectures_dir(config)
    output_path = lectures_dir / filename
    subject_value = subject or "General"

    alias_list = list(aliases or [])
    if safe_name not in alias_list:
        alias_list.insert(0, safe_name)
    aliases_yaml = "[" + ", ".join(f'"{a}"' for a in alias_list) + "]"

    source_line = ""
    if source_audio is not None:
        source_line = f'source_audio: "{source_audio}"\n'

    moc_line = ""
    if (config.moc_note or "").strip():
        moc_safe = sanitize_lecture_name(config.moc_note)
        moc_line = f'moc: "[[{moc_safe}]]"\n'

    frontmatter = (
        "---\n"
        f'date: "{date_str}"\n'
        f'time: "{time_str}"\n'
        "type: lecture\n"
        f'subject: "{subject_value}"\n'
        f"aliases: {aliases_yaml}\n"
        "tags: [lecture, audio-transcribed]\n"
        f"{source_line}"
        f"{moc_line}"
        "---\n\n"
    )
    body = content if content.endswith("\n") else content + "\n"
    payload = frontmatter + body

    try:
        output_path.write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise VaultWriteError(
            f"Failed to write note to {output_path}: {exc}. "
            "Check that the Obsidian vault path is writable "
            "(and not locked by Sync on another device)."
        ) from exc

    logger.info("Wrote lecture note to %s", output_path)

    if transcript and config.save_transcript:
        save_transcript_sidecar(transcript, output_path)

    update_moc(config, output_path, subject_value, date_str)
    return output_path
