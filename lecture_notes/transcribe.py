"""Local Whisper transcription for lecture audio files."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from lecture_notes.errors import TranscriptionError

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg"}

_model_cache: dict[str, object] = {}


@dataclass
class TranscriptSegment:
    """A timed Whisper segment."""

    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    """Full transcript plus timed segments for chunked structuring."""

    text: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    source_path: Path | None = None


def _get_model(model_size: str) -> object:
    """Load and cache a Whisper model by size."""
    if model_size in _model_cache:
        return _model_cache[model_size]

    try:
        import whisper
    except ImportError as exc:
        raise TranscriptionError(
            "openai-whisper is not installed. Run: pip install -e ."
        ) from exc

    try:
        logger.info(
            "Loading Whisper model '%s' (first load may take a while)", model_size
        )
        model = whisper.load_model(model_size)
    except Exception as exc:  # noqa: BLE001 — surface as actionable error
        raise TranscriptionError(
            f"Failed to load Whisper model '{model_size}': {exc}"
        ) from exc

    _model_cache[model_size] = model
    return model


def preprocess_audio(audio_path: Path) -> Path:
    """Normalize loudness and trim long silences with ffmpeg.

    Returns a temporary WAV path the caller should delete when finished.
    Raises :class:`TranscriptionError` if ffmpeg is missing or fails.
    """
    if shutil.which("ffmpeg") is None:
        raise TranscriptionError(
            "ffmpeg not found on PATH. Install ffmpeg to preprocess audio "
            "(or set ffmpeg_preprocess: false in config.yaml)."
        )

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    # loudnorm + light silence trim (keeps short pauses, drops long gaps)
    filters = (
        "loudnorm=I=-16:TP=-1.5:LRA=11,"
        "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-40dB:"
        "stop_periods=-1:stop_silence=1.0:stop_threshold=-40dB"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-af",
        filters,
        "-ar",
        "16000",
        "-ac",
        "1",
        str(tmp_path),
    ]
    try:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        raise TranscriptionError(f"Failed to run ffmpeg: {exc}") from exc

    if completed.returncode != 0 or not tmp_path.is_file() or tmp_path.stat().st_size == 0:
        err = (completed.stderr or completed.stdout or "").strip()
        tmp_path.unlink(missing_ok=True)
        raise TranscriptionError(
            f"ffmpeg preprocess failed for {audio_path}: {err or 'unknown error'}"
        )

    logger.info("Preprocessed audio → %s", tmp_path)
    return tmp_path


def transcribe_audio(
    audio_path: Path,
    model_size: str = "small",
    language: str = "en",
    preprocess: bool = False,
) -> TranscriptResult:
    """Transcribe an audio file using a local Whisper model.

    Supported extensions: ``.wav``, ``.mp3``, ``.m4a``, ``.ogg``.
    The loaded model is cached at module level for watcher reuse.
    When ``preprocess`` is True, runs ffmpeg loudness/silence cleanup first.
    """
    path = Path(audio_path)
    if not path.is_file():
        raise TranscriptionError(f"Audio file not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise TranscriptionError(
            f"Unsupported audio format '{suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    work_path = path
    temp_path: Path | None = None
    if preprocess:
        temp_path = preprocess_audio(path)
        work_path = temp_path

    model = _get_model(model_size)

    try:
        logger.info(
            "Transcribing %s (language=%s, model=%s)", work_path, language, model_size
        )
        result = model.transcribe(  # type: ignore[attr-defined]
            str(work_path),
            language=language or None,
            verbose=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise TranscriptionError(
            f"Transcription failed for {path}: {exc}. "
            "Ensure ffmpeg is installed and the file is a valid audio recording."
        ) from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    if not isinstance(result, dict):
        raise TranscriptionError(f"Unexpected Whisper result type for {path}")

    text = (result.get("text") or "").strip()
    if not text:
        raise TranscriptionError(
            f"Whisper returned an empty transcript for {path}. "
            "Check that the recording contains speech."
        )

    segments: list[TranscriptSegment] = []
    for seg in result.get("segments") or []:
        if not isinstance(seg, dict):
            continue
        seg_text = (seg.get("text") or "").strip()
        if not seg_text:
            continue
        segments.append(
            TranscriptSegment(
                start=float(seg.get("start") or 0.0),
                end=float(seg.get("end") or 0.0),
                text=seg_text,
            )
        )

    logger.info(
        "Transcription complete (%d characters, %d segments)",
        len(text),
        len(segments),
    )
    return TranscriptResult(text=text, segments=segments, source_path=path)
