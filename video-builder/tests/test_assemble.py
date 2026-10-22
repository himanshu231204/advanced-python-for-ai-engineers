import json
import subprocess
import wave
from pathlib import Path

import pytest
from PIL import Image

from bityodha.assemble import (
    DurationError,
    SceneClip,
    build_video,
    check_duration,
    format_chapters,
)


def test_check_duration_accepts_bounds():
    check_duration(315)
    check_duration(585)


@pytest.mark.parametrize("total", [314, 586])
def test_check_duration_rejects_outside(total):
    with pytest.raises(DurationError, match="5:15"):
        check_duration(total)


def test_format_chapters_starts_at_zero():
    text = format_chapters([("Intro", 0), ("Data", 12.4), ("Wrap", 75.0)])
    assert text.splitlines() == ["0:00 Intro", "0:12 Data", "1:15 Wrap"]


def test_format_chapters_rejects_fewer_than_three():
    with pytest.raises(ValueError, match="three"):
        format_chapters([("A", 0), ("B", 20)])


def test_format_chapters_rejects_chapter_under_10s():
    with pytest.raises(ValueError, match="10"):
        format_chapters([("A", 0), ("B", 5), ("C", 30)])


def _clip(tmp_path: Path, name: str, color: str, seconds: float) -> SceneClip:
    frames = tmp_path / name
    frames.mkdir()
    Image.new("RGB", (1920, 1080), color).save(frames / "f_0001.png")
    wav = tmp_path / f"{name}.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(b"\x00\x00" * int(22050 * seconds))
    return SceneClip(frames_dir=frames, fps=30, wav=wav, duration=seconds)


def test_build_video_produces_mp4(tmp_path):
    out = tmp_path / "v.mp4"
    build_video([_clip(tmp_path, "a", "red", 1.0), _clip(tmp_path, "b", "blue", 1.5)], out)
    probe = json.loads(
        subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(out)],
            capture_output=True, text=True, check=True,
        ).stdout
    )
    codecs = {s["codec_name"] for s in probe["streams"]}
    assert {"h264", "aac"} <= codecs
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (1920, 1080)
    assert float(probe["format"]["duration"]) == pytest.approx(2.5, abs=0.3)
