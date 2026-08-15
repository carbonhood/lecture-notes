"""Tests for Ollama note-structuring helpers."""

from __future__ import annotations

from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from lecture_notes.errors import StructuringError
from lecture_notes.structure import (
    NOTE_PROMPT_TEMPLATE,
    chunk_plain_text,
    chunk_segments,
    structure_notes,
)
from lecture_notes.transcribe import TranscriptSegment


def test_empty_transcript_raises() -> None:
    with pytest.raises(StructuringError, match="empty transcript"):
        structure_notes("   ")


def test_prompt_requires_obsidian_latex() -> None:
    assert "$...$" in NOTE_PROMPT_TEMPLATE
    assert "$$...$$" in NOTE_PROMPT_TEMPLATE
    assert "LaTeX Suite" in NOTE_PROMPT_TEMPLATE
    assert "never for equations" in NOTE_PROMPT_TEMPLATE.lower() or (
        "ONLY for programming code" in NOTE_PROMPT_TEMPLATE
    )


@patch("lecture_notes.structure.subprocess.run")
def test_prompt_includes_subject_and_transcript(mock_run) -> None:
    mock_run.return_value = CompletedProcess(
        args=[],
        returncode=0,
        stdout="## Topic\n\n- point\n\n$$E=mc^2$$\n",
        stderr="",
    )
    result = structure_notes("raw words", subject="Physics", llm_model="mistral")
    assert "## Topic" in result
    args = mock_run.call_args[0][0]
    assert args[:3] == ["ollama", "run", "mistral"]
    prompt = args[3]
    assert "Physics" in prompt
    assert "raw words" in prompt


@patch("lecture_notes.structure.subprocess.run")
def test_strips_wrapping_code_fence(mock_run) -> None:
    fenced = "```markdown\n## Main\n\n- a\n```\n"
    mock_run.return_value = CompletedProcess(
        args=[], returncode=0, stdout=fenced, stderr=""
    )
    result = structure_notes("transcript here")
    assert result.startswith("## Main")
    assert "```" not in result


@patch("lecture_notes.structure.subprocess.run")
def test_ollama_failure_raises(mock_run) -> None:
    mock_run.return_value = CompletedProcess(
        args=[], returncode=1, stdout="", stderr="model not found"
    )
    with pytest.raises(StructuringError, match="Ollama failed"):
        structure_notes("hello")


@patch("lecture_notes.structure.subprocess.run", side_effect=FileNotFoundError())
def test_ollama_missing_raises(_mock_run) -> None:
    with pytest.raises(StructuringError, match="Ollama CLI not found"):
        structure_notes("hello")


def test_chunk_segments_by_time() -> None:
    segs = [
        TranscriptSegment(0, 100, "a"),
        TranscriptSegment(100, 200, "b"),
        TranscriptSegment(200, 350, "c"),
        TranscriptSegment(350, 400, "d"),
    ]
    chunks = chunk_segments(segs, chunk_seconds=250)
    assert len(chunks) >= 2
    assert "a" in chunks[0]


def test_chunk_plain_text() -> None:
    text = ("word. " * 2000).strip()
    chunks = chunk_plain_text(text, max_chars=500)
    assert len(chunks) > 1
    assert "".join(chunks).replace(" ", "")[:20] in text.replace(" ", "")


@patch("lecture_notes.structure._run_ollama")
def test_multi_chunk_merge(mock_run) -> None:
    mock_run.side_effect = [
        "## Part A\n- a",
        "## Part B\n- b",
        "## Merged\n\n- a\n- b\n\n## Key Takeaways\n\n- one\n- two\n- three",
    ]
    segs = [
        TranscriptSegment(0, 10, "alpha " * 20),
        TranscriptSegment(700, 710, "beta " * 20),
    ]
    result = structure_notes(
        "alpha beta",
        subject="Math",
        segments=segs,
        chunk_seconds=100,
    )
    assert "Merged" in result
    assert mock_run.call_count == 3
