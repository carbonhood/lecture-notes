"""Watch a folder for new lecture recordings and process them automatically."""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lecture_notes.config import Config
from lecture_notes.errors import StructuringError, TranscriptionError, VaultWriteError
from lecture_notes.pipeline import process_audio_file
from lecture_notes.transcribe import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

STABILITY_SECONDS = 2.0
STABILITY_POLL = 0.5

# Incomplete / temp names from recorders, browsers, and sync clients
_IGNORE_SUFFIXES = {
    ".part",
    ".tmp",
    ".temp",
    ".crdownload",
    ".download",
    ".partial",
}
_IGNORE_NAME_PREFIXES = (".", "~", "._")


def is_temp_or_incomplete(path: Path) -> bool:
    """Return True for temp / partial download names that should be ignored."""
    name = path.name
    lower = name.lower()
    if any(lower.endswith(suf) for suf in _IGNORE_SUFFIXES):
        return True
    if name.startswith(_IGNORE_NAME_PREFIXES):
        return True
    if lower.endswith(".wav.part") or lower.endswith(".m4a.part"):
        return True
    return False


def wait_until_stable(path: Path, seconds: float = STABILITY_SECONDS) -> bool:
    """Return True once file size is unchanged for ``seconds``.

    Returns False if the file disappears before becoming stable.
    """
    try:
        last_size = path.stat().st_size
    except OSError:
        return False

    stable_for = 0.0
    while stable_for < seconds:
        time.sleep(STABILITY_POLL)
        try:
            size = path.stat().st_size
        except OSError:
            return False
        if size == last_size:
            stable_for += STABILITY_POLL
        else:
            last_size = size
            stable_for = 0.0
    return True


def move_to_processed(audio_path: Path, watch_folder: Path) -> Path:
    """Move a processed audio file into ``watch_folder/processed/``."""
    processed_dir = watch_folder / "processed"
    try:
        processed_dir.mkdir(parents=True, exist_ok=True)
        destination = processed_dir / audio_path.name
        if destination.exists():
            stamp = int(time.time())
            destination = processed_dir / f"{audio_path.stem}_{stamp}{audio_path.suffix}"
        shutil.move(str(audio_path), str(destination))
    except OSError as exc:
        raise VaultWriteError(
            f"Processed notes were saved, but could not move {audio_path} "
            f"to processed/: {exc}"
        ) from exc
    logger.info("Moved processed audio to %s", destination)
    return destination


class _AudioHandler(FileSystemEventHandler):
    def __init__(
        self, config: Config, subject: str, *, draft: bool = False
    ) -> None:
        super().__init__()
        self.config = config
        self.subject = subject
        self.draft = draft
        self._seen: set[str] = set()

    def on_created(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.is_directory:
            return
        path = Path(event.src_path)
        if is_temp_or_incomplete(path):
            logger.debug("Ignoring temp/incomplete file: %s", path.name)
            return
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        try:
            if "processed" in path.relative_to(self.config.watch_folder).parts:
                return
        except ValueError:
            pass

        key = str(path.resolve()) if path.exists() else str(path)
        if key in self._seen:
            return
        self._seen.add(key)

        logger.info("Detected new audio: %s", path.name)
        if not wait_until_stable(path):
            logger.warning("Skipping %s: file disappeared before stable", path.name)
            self._seen.discard(key)
            return
        # Re-check after stability in case a .part was renamed mid-write
        if is_temp_or_incomplete(path):
            self._seen.discard(key)
            return

        try:
            logger.info("Transcribing %s...", path.name)
            out = process_audio_file(
                path, self.config, subject=self.subject, draft=self.draft
            )
            logger.info("Structuring + saving done → %s", out)
            moved = move_to_processed(path, self.config.watch_folder)
            logger.info("Moved audio to %s", moved)
        except (TranscriptionError, StructuringError, VaultWriteError) as exc:
            logger.error("Error processing %s: %s", path.name, exc)
            self._seen.discard(key)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected watcher error for %s: %s", path.name, exc)
            self._seen.discard(key)


def watch_folder(
    config: Config, subject: str = "General", *, draft: bool = False
) -> None:
    """Monitor ``config.watch_folder`` and auto-process new audio files.

    Blocks until interrupted with Ctrl+C. Processed files are moved to a
    ``processed/`` subfolder so they are not handled again.
    """
    folder = Path(config.watch_folder)
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise VaultWriteError(
            f"Cannot create or access watch folder {folder}: {exc}"
        ) from exc

    handler = _AudioHandler(config, subject, draft=draft)
    observer = Observer()
    observer.schedule(handler, str(folder), recursive=False)
    observer.start()
    logger.info("Watching %s for new audio (Ctrl+C to stop)", folder)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
    finally:
        observer.stop()
        observer.join()
        logger.info("Watcher stopped.")
