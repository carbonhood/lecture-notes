"""Setuptools packaging for the lecture-notes CLI."""

from pathlib import Path

from setuptools import find_packages, setup

README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="lecture-notes",
    version="0.1.0",
    description="Local lecture audio → Whisper → Ollama → Obsidian notes",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "openai-whisper",
        "watchdog",
        "pyyaml",
    ],
    extras_require={
        "dev": ["pytest"],
    },
    entry_points={
        "console_scripts": [
            "lecture-notes=lecture_notes.cli:main",
        ],
    },
)
