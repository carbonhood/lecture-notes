"""Command-line entry point for lecture-notes."""

from __future__ import annotations

import argparse
import logging
import sys
import traceback
from pathlib import Path

import yaml

from lecture_notes.config import Config, load_config
from lecture_notes.errors import StructuringError, TranscriptionError, VaultWriteError
from lecture_notes.pipeline import (
    process_audio_file,
    resolve_whisper_model,
    restructure_transcript_file,
)
from lecture_notes.serve import serve_upload
from lecture_notes.watcher import watch_folder


def _configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _print_error(exc: BaseException, debug: bool) -> None:
    print(f"Error: {exc}", file=sys.stderr)
    if debug:
        traceback.print_exc()


def cmd_process(args: argparse.Namespace) -> int:
    """Run the one-shot pipeline on a single audio file."""
    config = load_config(Path(args.config) if args.config else None)
    audio = Path(args.audio_file)
    model = resolve_whisper_model(config, draft=args.draft)

    try:
        print(f"[1/3] Transcribing {audio} (Whisper '{model}'{', draft' if args.draft else ''})...")
        print(f"[2/3] Structuring notes (Ollama '{config.llm_model}', chunk={config.chunk_seconds}s)...")
        print("[3/3] Writing to Obsidian vault (+ transcript sidecar / MOC if enabled)...")
        output = process_audio_file(
            audio,
            config,
            subject=args.subject,
            lecture_name=args.lecture_name,
            date=args.date,
            draft=args.draft,
            language=args.language,
        )
    except (TranscriptionError, StructuringError, VaultWriteError) as exc:
        _print_error(exc, args.debug)
        return 1

    print(f"Done. Notes written to: {output}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    """Start folder-watching mode."""
    config = load_config(Path(args.config) if args.config else None)
    print(f"Watch folder: {config.watch_folder}")
    print(f"Vault: {config.vault_path / config.lectures_folder}")
    print("Starting watcher (Ctrl+C to stop)...")
    try:
        watch_folder(config, subject=args.subject, draft=args.draft)
    except (TranscriptionError, StructuringError, VaultWriteError) as exc:
        _print_error(exc, args.debug)
        return 1
    print("Watcher stopped.")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start mobile upload server for iPhone / iPad browsers."""
    config = load_config(Path(args.config) if args.config else None)
    bind_host = args.host or config.serve_host
    bind_port = args.port or config.serve_port
    from lecture_notes.serve import _guess_local_ip

    lan_ip = _guess_local_ip()
    print("Starting mobile upload server (processing stays on this computer)...")
    print(f"Mobile upload UI: http://{lan_ip}:{bind_port}/")
    print(f"Local only:       http://127.0.0.1:{bind_port}/")
    print(
        "On iPhone/iPad: join the same Wi‑Fi (or Tailscale), "
        "open the LAN URL in Safari."
    )
    print("Ctrl+C to stop.")
    try:
        serve_upload(
            config,
            subject=args.subject,
            host=bind_host,
            port=bind_port,
        )
    except (TranscriptionError, StructuringError, VaultWriteError) as exc:
        _print_error(exc, args.debug)
        return 1
    print("Upload server stopped.")
    return 0


def cmd_restructure(args: argparse.Namespace) -> int:
    """Rebuild notes from a saved .transcript.md without re-transcribing."""
    config = load_config(Path(args.config) if args.config else None)
    path = Path(args.transcript_file)
    print(f"Re-structuring from {path} (Ollama '{config.llm_model}')...")
    try:
        output = restructure_transcript_file(
            path,
            config,
            lecture_name=args.lecture_name,
            subject=args.subject,
            date=args.date,
        )
    except (StructuringError, VaultWriteError) as exc:
        _print_error(exc, args.debug)
        return 1
    print(f"Done. Notes written to: {output}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Interactive setup: write config.yaml in the current directory."""
    print("lecture-notes interactive setup")
    default_vault = str(Path("~/Obsidian Vault").expanduser())
    default_watch = str(Path("~/LectureRecordings").expanduser())

    vault = input(f"Obsidian vault path [{default_vault}]: ").strip() or default_vault
    watch = (
        input(f"Watch folder for recordings [{default_watch}]: ").strip()
        or default_watch
    )
    lectures = (
        input("Lectures folder name inside vault [Lectures]: ").strip() or "Lectures"
    )
    whisper = input("Whisper model size [small]: ").strip() or "small"
    draft = input("Whisper draft model [base]: ").strip() or "base"
    language = input("Whisper language [en]: ").strip() or "en"
    llm = input("Ollama LLM model [mistral]: ").strip() or "mistral"
    moc_raw = input(
        "MOC note name [Lectures MOC] (type - to disable): "
    ).strip()
    if moc_raw == "-":
        moc = ""
    elif moc_raw == "":
        moc = "Lectures MOC"
    else:
        moc = moc_raw

    data = {
        "vault_path": vault,
        "lectures_folder": lectures,
        "watch_folder": watch,
        "whisper_model": whisper,
        "whisper_draft_model": draft,
        "whisper_language": language,
        "llm_model": llm,
        "chunk_seconds": 600,
        "save_transcript": True,
        "ffmpeg_preprocess": True,
        "moc_note": moc,
        "serve_host": "0.0.0.0",
        "serve_port": 8787,
    }
    out = Path.cwd() / "config.yaml"
    try:
        out.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    except OSError as exc:
        _print_error(VaultWriteError(f"Could not write {out}: {exc}"), args.debug)
        return 1

    cfg: Config = load_config(out)
    print(f"Wrote {out}")
    print(f"  vault_path           = {cfg.vault_path}")
    print(f"  lectures_folder      = {cfg.lectures_folder}")
    print(f"  watch_folder         = {cfg.watch_folder}")
    print(f"  whisper_model        = {cfg.whisper_model}")
    print(f"  whisper_draft_model  = {cfg.whisper_draft_model}")
    print(f"  whisper_language     = {cfg.whisper_language}")
    print(f"  llm_model            = {cfg.llm_model}")
    print(f"  moc_note             = {cfg.moc_note!r}")
    print("Setup complete. You can edit config.yaml anytime.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="lecture-notes",
        description="Transcribe lecture audio and write Obsidian markdown notes.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show full tracebacks on errors",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    process_p = sub.add_parser("process", help="Process a single audio file")
    process_p.add_argument("audio_file", help="Path to audio (.wav/.mp3/.m4a/.ogg)")
    process_p.add_argument("lecture_name", help="Title used in the output filename")
    process_p.add_argument(
        "--subject", default="General", help="Subject tag/frontmatter"
    )
    process_p.add_argument(
        "--date", default=None, help="Override note date (YYYY-MM-DD)"
    )
    process_p.add_argument("--config", default=None, help="Path to config.yaml")
    process_p.add_argument(
        "--draft",
        action="store_true",
        help="Use whisper_draft_model (faster, lower quality)",
    )
    process_p.add_argument(
        "--language",
        default=None,
        help="Whisper language code (default: config whisper_language)",
    )
    process_p.set_defaults(func=cmd_process)

    watch_p = sub.add_parser("watch", help="Watch a folder for new recordings")
    watch_p.add_argument("--subject", default="General", help="Subject for new notes")
    watch_p.add_argument("--config", default=None, help="Path to config.yaml")
    watch_p.add_argument(
        "--draft",
        action="store_true",
        help="Use whisper_draft_model for watched files",
    )
    watch_p.set_defaults(func=cmd_watch)

    serve_p = sub.add_parser(
        "serve",
        help="Mobile upload server for iPhone/iPad (runs on this computer)",
    )
    serve_p.add_argument("--subject", default="General", help="Default subject")
    serve_p.add_argument("--config", default=None, help="Path to config.yaml")
    serve_p.add_argument("--host", default=None, help="Bind host (default from config)")
    serve_p.add_argument(
        "--port", type=int, default=None, help="Bind port (default from config)"
    )
    serve_p.set_defaults(func=cmd_serve)

    restr_p = sub.add_parser(
        "restructure",
        help="Rebuild notes from a .transcript.md sidecar (skip Whisper)",
    )
    restr_p.add_argument("transcript_file", help="Path to .transcript.md")
    restr_p.add_argument("lecture_name", help="Title for the output note")
    restr_p.add_argument("--subject", default="General")
    restr_p.add_argument("--date", default=None)
    restr_p.add_argument("--config", default=None)
    restr_p.set_defaults(func=cmd_restructure)

    init_p = sub.add_parser("init", help="Create config.yaml interactively")
    init_p.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point used by the ``lecture-notes`` console script."""
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.debug)
    try:
        code = args.func(args)
    except (TranscriptionError, StructuringError, VaultWriteError) as exc:
        _print_error(exc, args.debug)
        sys.exit(1)
    sys.exit(code)


if __name__ == "__main__":
    main()
