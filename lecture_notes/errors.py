"""Custom exceptions for the lecture-notes pipeline."""


class TranscriptionError(Exception):
    """Raised when audio transcription fails."""


class StructuringError(Exception):
    """Raised when LLM note structuring fails."""


class VaultWriteError(Exception):
    """Raised when writing notes to the Obsidian vault fails."""
