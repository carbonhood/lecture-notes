"""Tests for Obsidian vault writing."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lecture_notes.config import Config
from lecture_notes.errors import VaultWriteError
from lecture_notes.vault import sanitize_lecture_name, save_to_vault


def test_sanitize_illegal_characters() -> None:
    assert sanitize_lecture_name("Week 1: Intro/Overview?") == "Week 1_ Intro_Overview"


def test_sanitize_empty_raises() -> None:
    with pytest.raises(VaultWriteError, match="empty"):
        sanitize_lecture_name("   ???   ")


def test_save_to_vault_frontmatter_and_filename(tmp_path: Path) -> None:
    config = Config(
        vault_path=tmp_path / "vault",
        lectures_folder="Lectures",
        watch_folder=tmp_path / "watch",
        save_transcript=True,
        moc_note="Lectures MOC",
    )
    content = "## Intro\n\n- point one\n\n$$x^2$$\n"
    path = save_to_vault(
        content,
        lecture_name="Test Lecture",
        config=config,
        subject="Testing",
        date="2026-08-15",
        source_audio=tmp_path / "rec.wav",
        transcript="spoken words about x squared",
        aliases=["Test Lecture"],
    )

    assert path.name == "2026-08-15_Test Lecture.md"
    assert path.parent == config.vault_path / "Lectures"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    front = text.split("---\n", 2)[1]
    body = text.split("---\n", 2)[2]
    meta = yaml.safe_load(front)
    assert meta["date"] == "2026-08-15"
    assert meta["type"] == "lecture"
    assert meta["subject"] == "Testing"
    assert meta["tags"] == ["lecture", "audio-transcribed"]
    assert "Test Lecture" in meta["aliases"]
    assert "source_audio" in meta
    assert "moc" in meta
    assert "time" in meta
    assert "## Intro" in body

    sidecar = path.with_suffix(".transcript.md")
    assert sidecar.is_file()
    assert "spoken words" in sidecar.read_text(encoding="utf-8")

    moc = path.parent / "Lectures MOC.md"
    assert moc.is_file()
    assert "[[2026-08-15_Test Lecture]]" in moc.read_text(encoding="utf-8")
