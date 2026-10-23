"""Build a module video: python3 -m bityodha.build <module-folder-name>."""
import argparse
import math
import shutil
from pathlib import Path
from typing import Callable

from . import tts
from .assemble import SceneClip, build_video, check_duration, format_chapters
from .metadata import write_metadata
from .render import render_scene, render_thumbnail
from .runcode import run_example, slice_lines
from .spec import Scene, load_spec
from .theme import FPS

DELIVERABLES = ("video.mp4", "chapters.txt", "metadata.md", "thumbnail.png")
SCENE_PAD = 0.4
REVEAL_START = 0.5


def _write_frames(scene: Scene, code: str | None, output: str | None,
                  duration: float, frames_dir: Path) -> None:
    frames_dir.mkdir(parents=True)
    body = code if scene.type == "code" else output
    n = len(body.split("\n")) if body else 0
    if scene.type not in ("code", "output") or n == 0:
        render_scene(scene, code, output, 1.0).save(frames_dir / "f_0001.png")
        return
    reveal_end = max(REVEAL_START + 0.5, 0.7 * duration)
    first_of_state: dict[int, Path] = {}
    for k in range(int(reveal_end * FPS) + 1):
        t = k / FPS
        progress = min(1.0, max(0.0, (t - REVEAL_START) / (reveal_end - REVEAL_START)))
        lines = 0 if progress <= 0 else min(n, max(1, math.ceil(progress * n)))
        dest = frames_dir / f"f_{k + 1:04d}.png"
        if lines in first_of_state:
            shutil.copyfile(first_of_state[lines], dest)
            continue
        state_progress = 0.0 if lines == 0 else 1.0 if lines == n else (lines - 0.5) / n
        render_scene(scene, code, output, state_progress).save(dest)
        first_of_state[lines] = dest


def build_module(spec_path: Path, repo_root: Path, out_dir: Path,
                 voices_dir: Path | None = None,
                 synth: Callable[[str, Path | None, Path], float] = tts.synthesize,
                 check: Callable[[float], None] = check_duration) -> Path:
    spec = load_spec(spec_path, repo_root)
    work = out_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    for name in DELIVERABLES:
        (out_dir / name).unlink(missing_ok=True)
    voice = tts.ensure_voice(voices_dir) if voices_dir else None

    prepared = []
    for i, scene in enumerate(spec.scenes):
        path = repo_root / scene.file if scene.file else None
        code = slice_lines(path, scene.lines) if scene.type == "code" and scene.lines else None
        output = run_example(path) if path and (scene.run or scene.type == "output") else None
        if scene.type != "output":
            output = None
        wav = work / f"scene_{i:02d}.wav"
        seconds = synth(tts.apply_pronunciations(scene.narration, spec.pronunciations), voice, wav)
        prepared.append((scene, code, output, wav, seconds + SCENE_PAD))
        print(f"  narrated {scene.id}: {seconds:.1f}s")

    total = sum(p[4] for p in prepared)
    check(total)

    chapters, cursor = [], 0.0
    for scene, _, _, _, duration in prepared:
        if scene.chapter and (not chapters or chapters[-1][0] != scene.chapter):
            chapters.append((scene.chapter, cursor))
        cursor += duration
    if not chapters or chapters[0][1] != 0:
        chapters.insert(0, ("Intro", 0.0))
    chapters_text = format_chapters(chapters, total)

    clips = []
    for i, (scene, code, output, wav, duration) in enumerate(prepared):
        frames = work / f"scene_{i:02d}_frames"
        _write_frames(scene, code, output, duration, frames)
        clips.append(SceneClip(frames, FPS, wav, duration))

    build_video(clips, out_dir / "video.mp4")
    (out_dir / "chapters.txt").write_text(chapters_text + "\n")
    write_metadata(spec, chapters_text, out_dir)
    render_thumbnail(spec.title, f"MODULE {spec.module.split('-')[0]}").save(out_dir / "thumbnail.png")
    print(f"built {out_dir / 'video.mp4'} ({total / 60:.1f} min)")
    return out_dir / "video.mp4"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", help="module folder name, e.g. 00-python-foundation-review")
    args = parser.parse_args()
    builder = Path(__file__).resolve().parents[1]
    build_module(
        builder / "modules" / args.module / "scenes.yaml",
        builder.parent,
        builder / "out" / args.module,
        voices_dir=builder / "voices",
    )


if __name__ == "__main__":
    main()
