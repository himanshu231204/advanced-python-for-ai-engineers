"""Assemble scene clips into the final MP4 with ffmpeg; chapters and duration guard."""
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .spec import MAX_SECONDS, MIN_SECONDS

__all__ = ["MIN_SECONDS", "MAX_SECONDS", "DurationError", "SceneClip",
           "check_duration", "format_chapters", "build_video"]


class DurationError(RuntimeError):
    pass


@dataclass
class SceneClip:
    """frames_dir holds f_0001.png, f_0002.png, ...; the last frame is held to `duration`."""
    frames_dir: Path
    fps: int
    wav: Path
    duration: float


def _mmss(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def check_duration(total: float) -> None:
    if not MIN_SECONDS <= total <= MAX_SECONDS:
        raise DurationError(
            f"video is {_mmss(total)} but must be between "
            f"{_mmss(MIN_SECONDS)} and {_mmss(MAX_SECONDS)}"
        )


def format_chapters(chapters: list[tuple[str, float]]) -> str:
    if len(chapters) < 3:
        raise ValueError("YouTube chapters need at least three entries")
    for (title, start), (_, nxt) in zip(chapters, chapters[1:]):
        if nxt - start < 10:
            raise ValueError(f"chapter {title!r} is shorter than 10 seconds")
    return "\n".join(f"{_mmss(start)} {title}" for title, start in chapters)


def _ffmpeg(*args: str) -> None:
    proc = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr}")


def build_video(scene_clips: list[SceneClip], out_mp4: Path) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        segments = []
        for i, clip in enumerate(scene_clips):
            seg = Path(tmp) / f"seg_{i:03d}.mp4"
            _ffmpeg(
                "-framerate", str(clip.fps), "-i", str(clip.frames_dir / "f_%04d.png"),
                "-i", str(clip.wav),
                "-vf", f"tpad=stop_mode=clone:stop_duration={clip.duration},format=yuv420p",
                "-af", "apad", "-t", f"{clip.duration:.3f}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(clip.fps),
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
                str(seg),
            )
            segments.append(seg)
        listing = Path(tmp) / "list.txt"
        listing.write_text("".join(f"file '{s}'\n" for s in segments))
        _ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing),
                "-c", "copy", "-movflags", "+faststart", str(out_mp4))
