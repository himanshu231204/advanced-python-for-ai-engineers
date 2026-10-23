import shutil
import wave
from pathlib import Path

import pytest
import yaml

from bityodha.build import build_module
from bityodha.runcode import RunError


def silent_synth(seconds: float):
    def synth(text, voice, out_wav):
        with wave.open(str(out_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            w.writeframes(b"\x00\x00" * int(22050 * seconds))
        return seconds
    return synth


def make_repo(tmp_path: Path, bad: bool = False) -> tuple[Path, Path]:
    (tmp_path / "mod").mkdir()
    (tmp_path / "mod" / "ex.py").write_text("a = 1\nprint(a)\n")
    (tmp_path / "mod" / "bad.py").write_text("raise SystemExit(1)\n")
    words = " ".join(["word"] * 270)
    out_file = "mod/bad.py" if bad else "mod/ex.py"
    scenes = [
        {"id": "a", "type": "title", "chapter": "Intro", "heading": "Hello", "narration": words},
        {"id": "b", "type": "code", "chapter": "Code", "file": "mod/ex.py", "lines": [1, 2], "run": True, "narration": words},
        {"id": "c", "type": "output", "chapter": "Result", "file": out_file, "narration": words},
    ]
    spec = tmp_path / "scenes.yaml"
    spec.write_text(yaml.safe_dump({"module": "mod", "title": "T", "hashtags": ["ai"], "scenes": scenes}))
    return spec, tmp_path


def test_build_end_to_end_smoke(tmp_path):
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg missing")
    spec, repo = make_repo(tmp_path)
    out = tmp_path / "out"
    build_module(spec, repo, out, synth=silent_synth(11), check=lambda total: None)
    for name in ("video.mp4", "chapters.txt", "metadata.md", "thumbnail.png"):
        assert (out / name).is_file(), name
    assert (out / "chapters.txt").read_text().splitlines()[0] == "0:00 Intro"


def test_build_clears_stale_scene_files(tmp_path):
    spec, repo = make_repo(tmp_path)
    out = tmp_path / "out"
    (out / "work").mkdir(parents=True)
    stale = out / "work" / "scene_99.wav"
    stale.write_bytes(b"x")
    build_module(spec, repo, out, synth=silent_synth(11), check=lambda total: None)
    assert not stale.exists()


def test_build_stops_when_example_fails(tmp_path):
    spec, repo = make_repo(tmp_path, bad=True)
    with pytest.raises(RunError, match="bad.py"):
        build_module(spec, repo, tmp_path / "out", synth=silent_synth(11), check=lambda total: None)


def test_build_enforces_duration_guard(tmp_path):
    from bityodha.assemble import DurationError

    spec, repo = make_repo(tmp_path)
    with pytest.raises(DurationError):
        build_module(spec, repo, tmp_path / "out", synth=silent_synth(11))


def test_failed_build_removes_stale_deliverables(tmp_path):
    spec, repo = make_repo(tmp_path, bad=True)
    out = tmp_path / "out"
    out.mkdir()
    for name in ("video.mp4", "chapters.txt", "metadata.md", "thumbnail.png"):
        (out / name).write_text("old")
    with pytest.raises(RunError):
        build_module(spec, repo, out, synth=silent_synth(11), check=lambda total: None)
    assert [p.name for p in out.iterdir() if p.is_file()] == []
