"""YouTube metadata for a built video."""
from pathlib import Path

from .spec import ModuleSpec

REPO_URL = "https://github.com/himanshu231204/advanced-python-for-ai-engineers"
TAGLINE = "Learn in public. Build real projects. Share everything."
BASE_TAGS = ["python for ai engineers", "ai engineer", "advanced python", "bityodha"]


def write_metadata(spec: ModuleSpec, chapters_text: str, out_dir: Path) -> Path:
    number = spec.module.split("-")[0]
    topic = " ".join(spec.module.split("-")[1:])
    hashtags = " ".join(f"#{h}" for h in spec.hashtags)
    tags = ", ".join(BASE_TAGS + [topic] + spec.hashtags)
    text = f"""# Title

{spec.title}

# Description

{spec.title}

Module {number} of Advanced Python for AI Engineers: {topic}. Every code example
in this video is real, runnable code from the open-source repo.

Chapters:
{chapters_text}

Code and lessons: {REPO_URL}

{TAGLINE}

{hashtags}

# Tags

Tags: {tags}
"""
    path = out_dir / "metadata.md"
    path.write_text(text)
    return path
