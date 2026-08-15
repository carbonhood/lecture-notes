"""Local HTTP upload server for iPhone / iPad (and any browser).

Whisper and Ollama cannot run natively on iOS. Instead, run this server on
your desktop (Intel machine); Safari on iPhone/iPad uploads recordings over
the LAN (or Tailscale). Notes land in the Obsidian vault and sync via
Obsidian Sync.
"""

from __future__ import annotations

import logging
import re
import socket
import tempfile
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from lecture_notes.config import Config
from lecture_notes.errors import StructuringError, TranscriptionError, VaultWriteError
from lecture_notes.pipeline import process_audio_file
from lecture_notes.transcribe import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


@dataclass
class FormFile:
    """Uploaded file field from multipart/form-data."""

    filename: str
    data: bytes


@dataclass
class ParsedForm:
    """Parsed multipart form fields."""

    values: dict[str, str] = field(default_factory=dict)
    files: dict[str, FormFile] = field(default_factory=dict)


def _parse_multipart(content_type: str, body: bytes) -> ParsedForm:
    """Parse multipart/form-data without the deprecated ``cgi`` module."""
    match = re.search(r"boundary=([^;]+)", content_type, flags=re.IGNORECASE)
    if not match:
        raise ValueError("Missing multipart boundary")
    boundary = match.group(1).strip().strip('"').encode("ascii", errors="ignore")
    if not boundary:
        raise ValueError("Empty multipart boundary")

    form = ParsedForm()
    delimiter = b"--" + boundary
    parts = body.split(delimiter)
    for part in parts:
        if not part or part in (b"--", b"--\r\n", b"--\n"):
            continue
        if part.startswith(b"--"):
            continue
        if part.startswith(b"\r\n"):
            part = part[2:]
        elif part.startswith(b"\n"):
            part = part[1:]
        if part.endswith(b"\r\n"):
            part = part[:-2]
        elif part.endswith(b"\n"):
            part = part[:-1]

        header_blob, sep, data = part.partition(b"\r\n\r\n")
        if not sep:
            header_blob, sep, data = part.partition(b"\n\n")
        if not sep:
            continue
        headers = header_blob.decode("utf-8", errors="replace")
        disp = ""
        for line in headers.splitlines():
            if line.lower().startswith("content-disposition:"):
                disp = line
                break
        name_m = re.search(r'name="([^"]+)"', disp)
        if not name_m:
            continue
        name = name_m.group(1)
        filename_m = re.search(r'filename="([^"]*)"', disp)
        if filename_m is not None:
            form.files[name] = FormFile(
                filename=filename_m.group(1),
                data=data,
            )
        else:
            form.values[name] = data.decode("utf-8", errors="replace").strip()
    return form

UPLOAD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
  <meta name="apple-mobile-web-app-capable" content="yes"/>
  <title>Lecture Notes Upload</title>
  <style>
    :root {{
      --bg: #0f1419;
      --card: #1a222c;
      --text: #e8eef4;
      --muted: #8b9aab;
      --accent: #3d9cf0;
      --ok: #3ecf8e;
      --err: #f07178;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #1b3a57 0%, var(--bg) 55%);
      color: var(--text); min-height: 100vh; padding: 1.25rem;
    }}
    main {{ max-width: 28rem; margin: 0 auto; }}
    h1 {{ font-size: 1.5rem; margin: 0.5rem 0 0.25rem; }}
    p.lead {{ color: var(--muted); margin: 0 0 1.5rem; line-height: 1.4; }}
    form {{
      background: var(--card); border-radius: 1rem; padding: 1.25rem;
      display: grid; gap: 0.85rem;
    }}
    label {{ font-size: 0.85rem; color: var(--muted); display: grid; gap: 0.35rem; }}
    input[type=text], select {{
      font-size: 1rem; padding: 0.75rem 0.85rem; border-radius: 0.65rem;
      border: 1px solid #2c3a4a; background: #121820; color: var(--text);
    }}
    input[type=file] {{
      font-size: 1rem; padding: 0.75rem 0; color: var(--text);
    }}
    button {{
      font-size: 1.05rem; font-weight: 600; padding: 0.9rem 1rem;
      border: 0; border-radius: 0.75rem; background: var(--accent); color: #fff;
    }}
    button:disabled {{ opacity: 0.6; }}
    .row {{ display: flex; gap: 0.75rem; align-items: center; }}
    .row label {{ flex: 1; }}
    .msg {{ margin-top: 1rem; padding: 0.9rem 1rem; border-radius: 0.75rem; line-height: 1.4; }}
    .ok {{ background: rgba(62,207,142,0.12); color: var(--ok); }}
    .err {{ background: rgba(240,113,120,0.12); color: var(--err); }}
    .hint {{ font-size: 0.8rem; color: var(--muted); margin-top: 1.25rem; }}
  </style>
</head>
<body>
  <main>
    <h1>Lecture Notes</h1>
    <p class="lead">Upload a lecture recording from this iPhone/iPad. Processing runs on your desktop; notes sync into Obsidian.</p>
    <form id="f" action="/upload" method="post" enctype="multipart/form-data">
      <label>Audio file
        <input type="file" name="audio" accept="audio/*,.wav,.mp3,.m4a,.ogg" required capture="environment"/>
      </label>
      <label>Lecture name
        <input type="text" name="lecture_name" placeholder="Week 3 Linear Algebra" required/>
      </label>
      <label>Subject
        <input type="text" name="subject" value="{subject}" placeholder="General"/>
      </label>
      <div class="row">
        <label>Draft (faster Whisper)
          <select name="draft">
            <option value="0">No — use final model</option>
            <option value="1">Yes — draft model</option>
          </select>
        </label>
      </div>
      <button type="submit" id="btn">Upload &amp; process</button>
    </form>
    <div id="status"></div>
    <p class="hint">Keep this page open until processing finishes. Large lectures can take several minutes on CPU.</p>
  </main>
  <script>
    const form = document.getElementById('f');
    const btn = document.getElementById('btn');
    const status = document.getElementById('status');
    form.addEventListener('submit', async (e) => {{
      e.preventDefault();
      btn.disabled = true;
      status.innerHTML = '<div class="msg ok">Uploading &amp; processing… this can take a while.</div>';
      try {{
        const res = await fetch('/upload', {{ method: 'POST', body: new FormData(form) }});
        const text = await res.text();
        status.innerHTML = '<div class="msg ' + (res.ok ? 'ok' : 'err') + '">' + text + '</div>';
      }} catch (err) {{
        status.innerHTML = '<div class="msg err">Upload failed: ' + err + '</div>';
      }} finally {{
        btn.disabled = false;
      }}
    }});
  </script>
</body>
</html>
"""


def _guess_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def _make_handler(config: Config, default_subject: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:  # noqa: A003
            logger.info("%s - %s", self.address_string(), fmt % args)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                body = UPLOAD_HTML.format(subject=default_subject).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/health":
                payload = b"ok"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            self.send_error(404, "Not found")

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/upload":
                self.send_error(404, "Not found")
                return

            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self._text_response(400, "Expected multipart form upload.")
                return

            length = int(self.headers.get("Content-Length", "0") or 0)
            if length <= 0:
                self._text_response(400, "Empty upload.")
                return
            # Cap uploads at 500 MiB to protect the desktop host
            if length > 500 * 1024 * 1024:
                self._text_response(400, "Upload too large (max 500 MiB).")
                return

            try:
                body = self.rfile.read(length)
                form = _parse_multipart(content_type, body)
            except Exception as exc:  # noqa: BLE001
                self._text_response(400, f"Could not parse upload: {exc}")
                return

            audio_item = form.files.get("audio")
            if audio_item is None or not audio_item.data:
                self._text_response(400, "Missing audio file.")
                return

            lecture_name = form.values.get("lecture_name") or Path(
                audio_item.filename or "lecture"
            ).stem
            subject = form.values.get("subject") or default_subject
            draft = form.values.get("draft", "") in {"1", "true", "yes", "on"}

            suffix = Path(audio_item.filename or "").suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                self._text_response(
                    400,
                    f"Unsupported type '{suffix or 'unknown'}'. "
                    f"Use: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
                )
                return

            tmp_dir = Path(tempfile.mkdtemp(prefix="lecture-notes-upload-"))
            audio_path = tmp_dir / f"{uuid.uuid4().hex}{suffix}"
            try:
                audio_path.write_bytes(audio_item.data)
                note_path = process_audio_file(
                    audio_path,
                    config,
                    subject=subject,
                    lecture_name=lecture_name,
                    draft=draft,
                )
                msg = (
                    f"Done. Notes written to vault as {note_path.name}. "
                    "Open Obsidian on this device after Sync finishes."
                )
                self._text_response(200, msg)
            except (TranscriptionError, StructuringError, VaultWriteError) as exc:
                logger.error("Upload processing failed: %s", exc)
                self._text_response(500, f"Processing failed: {exc}")
            except Exception as exc:  # noqa: BLE001
                logger.exception("Unexpected upload error")
                self._text_response(500, f"Unexpected error: {exc}")
            finally:
                try:
                    audio_path.unlink(missing_ok=True)
                    tmp_dir.rmdir()
                except OSError:
                    pass

        def _text_response(self, code: int, message: str) -> None:
            body = message.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve_upload(
    config: Config,
    subject: str = "General",
    host: str | None = None,
    port: int | None = None,
) -> tuple[str, int, str]:
    """Start the mobile-friendly upload server (blocking).

    Returns ``(bind_host, bind_port, lan_ip)`` after shutdown for callers that
    printed connection details up front.
    """
    bind_host = host or config.serve_host
    bind_port = port or config.serve_port
    handler = _make_handler(config, subject)
    server = ThreadingHTTPServer((bind_host, bind_port), handler)
    lan_ip = _guess_local_ip()
    logger.info("Mobile upload server on http://%s:%s/ (LAN %s)", bind_host, bind_port, lan_ip)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping upload server...")
    finally:
        server.server_close()
        logger.info("Upload server stopped.")
    return bind_host, bind_port, lan_ip