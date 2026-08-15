"""Tests for Whisper transcription helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lecture_notes.errors import TranscriptionError
from lecture_notes.transcribe import SUPPORTED_EXTENSIONS, TranscriptResult, transcribe_audio


def test_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.wav"
    with pytest.raises(TranscriptionError, match="not found"):
        transcribe_audio(missing)


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    bad = tmp_path / "notes.txt"
    bad.write_text("not audio", encoding="utf-8")
    with pytest.raises(TranscriptionError, match="Unsupported audio format"):
        transcribe_audio(bad)


def test_supported_extensions_listed() -> None:
    assert {".wav", ".mp3", ".m4a", ".ogg"} == SUPPORTED_EXTENSIONS


@patch("lecture_notes.transcribe._get_model")
def test_transcribe_success(mock_get_model: MagicMock, tmp_path: Path) -> None:
    audio = tmp_path / "lecture.wav"
    audio.write_bytes(b"RIFF")
    model = MagicMock()
    model.transcribe.return_value = {
        "text": "  Hello lecture world  ",
        "segments": [
            {"start": 0.0, "end": 1.5, "text": " Hello"},
            {"start": 1.5, "end": 3.0, "text": " lecture world"},
        ],
    }
    mock_get_model.return_value = model

    result = transcribe_audio(audio, model_size="small", language="en")
    assert isinstance(result, TranscriptResult)
    assert result.text == "Hello lecture world"
    assert len(result.segments) == 2
    model.transcribe.assert_called_once()
    kwargs = model.transcribe.call_args
    assert kwargs.kwargs.get("language") == "en" or (
        len(kwargs.args) >= 1 and kwargs.kwargs.get("language") == "en"
    )


@patch("lecture_notes.transcribe._get_model")
def test_empty_transcript_raises(mock_get_model: MagicMock, tmp_path: Path) -> None:
    audio = tmp_path / "silent.mp3"
    audio.write_bytes(b"ID3")
    model = MagicMock()
    model.transcribe.return_value = {"text": "   ", "segments": []}
    mock_get_model.return_value = model

    with pytest.raises(TranscriptionError, match="empty transcript"):
        transcribe_audio(audio)


@patch("lecture_notes.transcribe.shutil.which", return_value=None)
def test_preprocess_requires_ffmpeg(_which: MagicMock, tmp_path: Path) -> None:
    from lecture_notes.transcribe import preprocess_audio

    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    with pytest.raises(TranscriptionError, match="ffmpeg not found"):
        preprocess_audio(audio)
