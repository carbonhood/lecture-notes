# Local Lecture Note-Taker → Obsidian

Transcribe lecture recordings with a local Whisper model, structure them into
clean Obsidian markdown (with `$...$` / `$$...$$` math) via Ollama, and write
straight into your Obsidian vault — offline after model downloads.

Designed for CPU-only desktops (e.g. Intel i9 + 32GB RAM) using Whisper `small`
and Mistral via Ollama. **iPhone / iPad cannot run Whisper or Ollama natively**;
use `lecture-notes serve` on your computer and upload from Safari (notes sync
via Obsidian Sync).

## Prerequisites

- **Python 3.10+** (on your Mac/Windows/Linux desktop — not on iOS)
- **[Ollama](https://ollama.com)** installed separately: `ollama pull mistral`
- **ffmpeg** on PATH (Whisper formats + optional preprocess)
- An Obsidian vault on disk (Obsidian Sync is fine — point `vault_path` at it)

## Install

```bash
cd lecture-notes
pip install -e .
pip install -e ".[dev]"   # optional, for pytest
lecture-notes --help
```

## Quick start: `lecture-notes init`

```bash
lecture-notes init
```

Writes `config.yaml` (vault path, watch folder, Whisper/LLM models, MOC name,
chunk size, mobile serve port, etc.). Or copy `config.example.yaml`.

## Usage

### Process one recording

```bash
lecture-notes process ./recording.wav "Week 3 Linear Algebra" --subject Math
# faster draft pass:
lecture-notes process ./recording.wav "Draft" --subject Math --draft
```

### Watch a folder

```bash
lecture-notes watch --subject Math
```

Ignores temp/partial names (`.part`, `.tmp`, `.crdownload`, `~…`). Waits until
file size is stable for 2s, then processes and moves audio to `processed/`.

### iPhone / iPad upload (recommended mobile path)

On your **desktop** (same Wi‑Fi, or [Tailscale](https://tailscale.com)):

```bash
lecture-notes serve --subject Math
```

Open the printed LAN URL in **Safari** on your iPhone/iPad, pick a Voice Memo
(`.m4a`) or recording, and submit. Processing runs on the desktop; the note
appears in the vault and syncs to Obsidian mobile.

### Re-structure without re-transcribing

```bash
lecture-notes restructure ./vault/Lectures/2026-08-15_Lecture.transcript.md "Lecture"
```

## What the pipeline does

1. **Optional ffmpeg preprocess** — loudness normalize + light silence trim
2. **Whisper** — language pinned (default `en`); `--draft` uses `whisper_draft_model` (`base`)
3. **Chunked Ollama structuring** — long lectures split by Whisper segment times (`chunk_seconds`, default 600), then merged
4. **Obsidian math** — equations as `$...$` / `$$...$$` (renders in Obsidian; editable later with LaTeX Suite)
5. **Vault write** — frontmatter (`aliases`, `source_audio`, `moc`), optional `.transcript.md` sidecar, MOC index update

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Ollama CLI / empty notes | Install Ollama, `ollama serve`, `ollama pull mistral` |
| ffmpeg / preprocess errors | Install ffmpeg, or set `ffmpeg_preprocess: false` |
| iPhone cannot open upload page | Same Wi‑Fi/Tailscale; allow port `serve_port` (default 8787) on the firewall |
| Math shows as code | Ensure notes use `$`/`$$` (current prompt); re-run `restructure` on the sidecar |
| Vault permissions | Check `vault_path` is writable |

## Development

```bash
pip install -e ".[dev]"
pytest
```
