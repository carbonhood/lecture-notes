# Local Lecture Note-Taker → Obsidian

Transcribe lecture recordings with a local Whisper model, structure them into
clean Obsidian markdown (with `$...$` / `$$...$$` math) via Ollama, and write
straight into your Obsidian vault — offline after model downloads.

Designed for CPU-only desktops (e.g. Intel i9 + 32GB RAM) using Whisper `small`
and Mistral via Ollama. **iPhone / iPad cannot run Whisper or Ollama natively**;
use `lecture-notes serve` on your computer and upload from Safari (notes sync
via Obsidian Sync).

## Setup walkthrough

### 1. Prerequisites

Install these on your **desktop** (Mac / Windows / Linux — not on iOS):

| Tool | Why |
| --- | --- |
| **Python 3.10+** | Runs the `lecture-notes` CLI |
| **[Ollama](https://ollama.com)** | Structures transcripts into Obsidian notes (`ollama pull mistral`) |
| **ffmpeg** | Audio format support + optional loudness/silence preprocess |
| **Obsidian vault** on disk | Output destination (`vault_path`; Obsidian Sync is fine) |

Confirm Ollama is up before the first real run:

```bash
ollama serve          # if it is not already running
ollama pull mistral
ollama list           # should show mistral
```

### 2. Install the package

From this repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
pip install -e ".[dev]"     # optional, for pytest
lecture-notes --help
```

### 3. Create `config.yaml`

Interactive (recommended):

```bash
lecture-notes init
```

Or copy the example and edit paths:

```bash
cp config.example.yaml config.yaml
```

Important keys:

- `vault_path` — your Obsidian vault folder
- `watch_folder` — where new recordings land (watcher / serve drop zone)
- `whisper_model` / `llm_model` — defaults `small` / `mistral`
- `save_transcript` — keep a `.transcript.md` sidecar for later restructure

`config.yaml` is gitignored so local paths stay private.

### 4. Smoke-test without audio (example transcript)

This repo ships a sample Whisper-style transcript you can structure with Ollama
(no recording needed):

```text
examples/2026-08-15_Week3_Linear_Algebra.transcript.md
```

```bash
lecture-notes restructure \
  examples/2026-08-15_Week3_Linear_Algebra.transcript.md \
  "Week 3 Linear Algebra" \
  --subject Math
```

Open your vault’s `Lectures/` folder in Obsidian — you should see the new note
(and a MOC update if `moc_note` is set).

### 5. Process a real recording

```bash
lecture-notes process ./recording.wav "Week 3 Linear Algebra" --subject Math
# faster draft pass (Whisper base):
lecture-notes process ./recording.wav "Draft" --subject Math --draft
```

### 6. Watch a folder (auto-ingest)

```bash
lecture-notes watch --subject Math
```

Drop `.wav` / `.m4a` / etc. into `watch_folder`. The watcher ignores temp names
(`.part`, `.tmp`, `.crdownload`, `~…`), waits until size is stable for 2s,
processes, then moves audio to `processed/`.

### 7. iPhone / iPad upload

On the **desktop** (same Wi‑Fi, or [Tailscale](https://tailscale.com)):

```bash
lecture-notes serve --subject Math
```

Open the printed LAN URL in **Safari**, upload a Voice Memo, and submit.
Processing runs on the desktop; the note appears in the vault and syncs to
Obsidian mobile.

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
