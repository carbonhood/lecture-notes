"""Structure raw transcripts into Obsidian-ready markdown via Ollama."""

from __future__ import annotations

import logging
import re
import subprocess

from lecture_notes.errors import StructuringError
from lecture_notes.transcribe import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)

NOTE_PROMPT_TEMPLATE = """You are an expert lecture note-taker. Convert the transcript
below into clean Obsidian markdown notes for the subject "{subject}".

Formatting rules (follow all of them):
- Start with one H2 main topic heading (# is reserved for the note title elsewhere)
- Use H3 headings for sections
- Use bullets and nested sub-bullets for concepts
- Write ALL math in Obsidian LaTeX: inline $...$ and display $$...$$
  (compatible with Obsidian MathJax and the LaTeX Suite plugin when editing later)
- Reconstruct spoken math into proper LaTeX (e.g. "x squared over 2" → $\\frac{{x^{{2}}}}{{2}}$)
- Use fenced code blocks ONLY for programming code, never for equations
- Put definitions in blockquotes
- Add [[Obsidian links]] for related concepts where helpful
- End with a "Key Takeaways" section containing 3-5 bullets
- Return ONLY markdown. No preamble, no explanation, no wrapping the whole
  response in a single markdown code fence.

{chunk_note}
Transcript:
{transcript}
"""

CHUNK_MERGE_PROMPT = """You are merging partial lecture notes into one coherent Obsidian note
for the subject "{subject}".

Rules:
- Produce a single polished note with one H2 main topic and H3 sections
- Deduplicate repeated points; keep the best wording
- Preserve all math as $...$ / $$...$$ (never code fences for equations)
- Keep [[wikilinks]], blockquotes for definitions, and code fences only for code
- End with one "Key Takeaways" section (3-5 bullets)
- Return ONLY markdown, no preamble

Partial notes to merge:
{partials}
"""

_FENCE_RE = re.compile(
    r"^```(?:markdown|md)?\s*\n?(.*?)\n?```\s*$", re.DOTALL | re.IGNORECASE
)


def _strip_stray_fences(text: str) -> str:
    """Remove a single outer markdown code fence if the model wrapped output."""
    stripped = text.strip()
    match = _FENCE_RE.match(stripped)
    if match:
        return match.group(1).strip()
    lines = stripped.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _run_ollama(llm_model: str, prompt: str) -> str:
    """Call ``ollama run`` and return cleaned stdout."""
    try:
        completed = subprocess.run(
            ["ollama", "run", llm_model, prompt],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise StructuringError(
            "Ollama CLI not found. Install Ollama from https://ollama.com "
            "and ensure `ollama` is on your PATH."
        ) from exc
    except OSError as exc:
        raise StructuringError(f"Failed to run Ollama: {exc}") from exc

    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "").strip()
        hint = err or (
            "Is the Ollama service running? "
            f"Try: ollama serve && ollama pull {llm_model}"
        )
        raise StructuringError(
            f"Ollama failed (exit {completed.returncode}) for model "
            f"'{llm_model}'. {hint}"
        )

    output = _strip_stray_fences(completed.stdout or "")
    if not output:
        raise StructuringError(
            f"Ollama returned empty notes for model '{llm_model}'. "
            f"Confirm the model is installed: ollama pull {llm_model}"
        )
    return output


def chunk_segments(
    segments: list[TranscriptSegment],
    chunk_seconds: int,
) -> list[str]:
    """Group timed segments into transcript chunks of about ``chunk_seconds``."""
    if chunk_seconds <= 0 or not segments:
        text = " ".join(s.text for s in segments).strip()
        return [text] if text else []

    chunks: list[str] = []
    current: list[str] = []
    chunk_start: float | None = None

    for seg in segments:
        if chunk_start is None:
            chunk_start = seg.start
        if seg.end - chunk_start >= chunk_seconds and current:
            chunks.append(" ".join(current).strip())
            current = [seg.text]
            chunk_start = seg.start
        else:
            current.append(seg.text)

    if current:
        chunks.append(" ".join(current).strip())
    return [c for c in chunks if c]


def chunk_plain_text(transcript: str, max_chars: int = 8000) -> list[str]:
    """Fallback chunking by character count when segments are unavailable."""
    text = transcript.strip()
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            split_at = text.rfind(". ", start, end)
            if split_at > start + max_chars // 2:
                end = split_at + 1
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]


def structure_notes(
    transcript: str,
    subject: str = "General",
    llm_model: str = "mistral",
    *,
    segments: list[TranscriptSegment] | None = None,
    chunk_seconds: int = 600,
) -> str:
    """Turn a plain transcript into structured markdown notes via Ollama.

    Long transcripts are split into time-based (or character-based) chunks,
    structured separately, then merged. Raises :class:`StructuringError` on
    subprocess failure or empty output.
    """
    if not transcript or not transcript.strip():
        raise StructuringError("Cannot structure an empty transcript.")

    if segments:
        pieces = chunk_segments(segments, chunk_seconds)
    else:
        # ~600s of speech ≈ a few thousand words; use char fallback
        pieces = chunk_plain_text(transcript)

    if not pieces:
        raise StructuringError("Cannot structure an empty transcript.")

    logger.info(
        "Structuring notes with Ollama model '%s' (%d chunk(s))",
        llm_model,
        len(pieces),
    )

    if len(pieces) == 1:
        prompt = NOTE_PROMPT_TEMPLATE.format(
            subject=subject,
            transcript=pieces[0],
            chunk_note="",
        )
        output = _run_ollama(llm_model, prompt)
        logger.info("Note structuring complete (%d characters)", len(output))
        return output

    partials: list[str] = []
    for index, piece in enumerate(pieces, start=1):
        logger.info("Structuring chunk %d/%d", index, len(pieces))
        prompt = NOTE_PROMPT_TEMPLATE.format(
            subject=subject,
            transcript=piece,
            chunk_note=(
                f"This is part {index} of {len(pieces)} of a longer lecture. "
                "Do NOT include a Key Takeaways section yet; focus on this part only.\n"
            ),
        )
        partials.append(_run_ollama(llm_model, prompt))

    merged_prompt = CHUNK_MERGE_PROMPT.format(
        subject=subject,
        partials="\n\n---\n\n".join(
            f"### Partial {i}\n{p}" for i, p in enumerate(partials, start=1)
        ),
    )
    output = _run_ollama(llm_model, merged_prompt)
    logger.info("Merged note structuring complete (%d characters)", len(output))
    return output


def structure_from_result(
    result: TranscriptResult,
    subject: str = "General",
    llm_model: str = "mistral",
    chunk_seconds: int = 600,
) -> str:
    """Structure notes from a :class:`TranscriptResult`."""
    return structure_notes(
        result.text,
        subject=subject,
        llm_model=llm_model,
        segments=result.segments,
        chunk_seconds=chunk_seconds,
    )
