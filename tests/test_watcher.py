"""Tests for watcher helpers."""

from pathlib import Path

from lecture_notes.watcher import is_temp_or_incomplete


def test_ignores_temp_names() -> None:
    assert is_temp_or_incomplete(Path("lecture.m4a.part"))
    assert is_temp_or_incomplete(Path("file.tmp"))
    assert is_temp_or_incomplete(Path(".hidden.wav"))
    assert is_temp_or_incomplete(Path("~draft.wav"))
    assert is_temp_or_incomplete(Path("video.crdownload"))
    assert not is_temp_or_incomplete(Path("lecture.wav"))
    assert not is_temp_or_incomplete(Path("lecture.m4a"))
