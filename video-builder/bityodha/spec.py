"""Load and validate a module's scene spec."""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SCENE_TYPES = {"title", "concept", "code", "output", "compare", "recap", "outro"}
WORDS_PER_MINUTE = 150
SCENE_PAD_SECONDS = 0.4
MIN_SECONDS = 315
MAX_SECONDS = 585


class SpecError(ValueError):
    pass


@dataclass
class Scene:
    id: str
    type: str
    narration: str
    chapter: str | None = None
    heading: str | None = None
    bullets: tuple[str, ...] = ()
    file: str | None = None
    lines: tuple[int, int] | None = None
    run: bool = False


@dataclass
class ModuleSpec:
    module: str
    title: str
    hashtags: list[str]
    scenes: list[Scene]
    pronunciations: dict[str, str] = field(default_factory=dict)


def estimate_seconds(spec: ModuleSpec) -> float:
    total_words = sum(len(s.narration.split()) for s in spec.scenes)
    return total_words / WORDS_PER_MINUTE * 60 + SCENE_PAD_SECONDS * len(spec.scenes)


def _mmss(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _build_scene(raw: dict, repo_root: Path) -> Scene:
    sid = str(raw.get("id", "?"))
    if raw.get("type") not in SCENE_TYPES:
        raise SpecError(f"scene {sid}: unknown type {raw.get('type')!r}")
    narration = str(raw.get("narration") or "").strip()
    if not narration:
        raise SpecError(f"scene {sid}: narration is empty")
    lines = raw.get("lines")
    file = raw.get("file")
    if raw["type"] == "code" and (not file or lines is None):
        raise SpecError(f"scene {sid}: code scenes need both file and lines")
    if raw["type"] == "output" and not file:
        raise SpecError(f"scene {sid}: output scenes need a file")
    if lines is not None and not (
        isinstance(lines, (list, tuple))
        and len(lines) == 2
        and all(isinstance(n, int) and not isinstance(n, bool) for n in lines)
    ):
        raise SpecError(f"scene {sid}: lines must be [start, end] integers")
    if file is not None:
        path = repo_root / file
        if not path.is_file():
            raise SpecError(f"scene {sid}: file not found: {file}")
        if lines is not None:
            start, end = lines
            count = len(path.read_text().splitlines())
            if not (1 <= start <= end <= count):
                raise SpecError(
                    f"scene {sid}: lines {start}-{end} invalid for {file} ({count} lines)"
                )
    return Scene(
        id=sid,
        type=raw["type"],
        narration=narration,
        chapter=raw.get("chapter"),
        heading=raw.get("heading"),
        bullets=tuple(raw.get("bullets") or ()),
        file=file,
        lines=tuple(lines) if lines else None,
        run=bool(raw.get("run", False)),
    )


def load_spec(path: Path, repo_root: Path) -> ModuleSpec:
    raw = yaml.safe_load(path.read_text())
    spec = ModuleSpec(
        module=raw["module"],
        title=raw["title"],
        hashtags=list(raw.get("hashtags") or []),
        scenes=[_build_scene(s, repo_root) for s in raw["scenes"]],
        pronunciations=dict(raw.get("pronunciations") or {}),
    )
    estimate = estimate_seconds(spec)
    if not MIN_SECONDS <= estimate <= MAX_SECONDS:
        raise SpecError(
            f"estimated length {_mmss(round(estimate))} is outside "
            f"{_mmss(MIN_SECONDS)}-{_mmss(MAX_SECONDS)}"
        )
    return spec
