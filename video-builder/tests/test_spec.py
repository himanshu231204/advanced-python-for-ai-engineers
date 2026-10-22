from pathlib import Path

import pytest
import yaml

from bityodha.spec import SpecError, estimate_seconds, load_spec


def words(n: int) -> str:
    return " ".join(["word"] * n)


def write_spec(tmp_path: Path, scenes: list[dict]) -> Path:
    (tmp_path / "mod").mkdir(exist_ok=True)
    (tmp_path / "mod" / "ex.py").write_text("a = 1\nb = 2\nc = 3\n")
    path = tmp_path / "scenes.yaml"
    path.write_text(
        yaml.safe_dump(
            {"module": "mod", "title": "T", "hashtags": ["ai"], "scenes": scenes}
        )
    )
    return path


def ok_scenes(total_words: int = 800) -> list[dict]:
    return [
        {"id": "a", "type": "title", "chapter": "Intro", "heading": "H", "narration": words(total_words // 2)},
        {"id": "b", "type": "concept", "chapter": "Body", "heading": "H", "narration": words(total_words // 2)},
    ]


def test_loads_valid_spec(tmp_path):
    spec = load_spec(write_spec(tmp_path, ok_scenes()), tmp_path)
    assert spec.module == "mod"
    assert [s.id for s in spec.scenes] == ["a", "b"]


def test_rejects_unknown_scene_type(tmp_path):
    scenes = ok_scenes()
    scenes[1]["type"] = "bogus"
    with pytest.raises(SpecError, match="b"):
        load_spec(write_spec(tmp_path, scenes), tmp_path)


def test_rejects_lines_past_end_of_file(tmp_path):
    scenes = ok_scenes()
    scenes.append({"id": "c", "type": "code", "file": "mod/ex.py", "lines": [1, 99], "narration": "x"})
    with pytest.raises(SpecError, match="c"):
        load_spec(write_spec(tmp_path, scenes), tmp_path)


def test_rejects_reversed_lines(tmp_path):
    scenes = ok_scenes()
    scenes.append({"id": "c", "type": "code", "file": "mod/ex.py", "lines": [3, 1], "narration": "x"})
    with pytest.raises(SpecError, match="c"):
        load_spec(write_spec(tmp_path, scenes), tmp_path)


def test_rejects_missing_file(tmp_path):
    scenes = ok_scenes()
    scenes.append({"id": "c", "type": "code", "file": "mod/nope.py", "lines": [1, 2], "narration": "x"})
    with pytest.raises(SpecError, match="c"):
        load_spec(write_spec(tmp_path, scenes), tmp_path)


def test_rejects_empty_narration(tmp_path):
    scenes = ok_scenes()
    scenes[0]["narration"] = "  "
    with pytest.raises(SpecError, match="a"):
        load_spec(write_spec(tmp_path, scenes), tmp_path)


def test_estimate_seconds_uses_150_wpm(tmp_path):
    spec = load_spec(write_spec(tmp_path, ok_scenes(800)), tmp_path)
    assert estimate_seconds(spec) == pytest.approx(800 / 150 * 60 + 0.4 * 2)


def test_rejects_estimate_outside_range(tmp_path):
    with pytest.raises(SpecError, match="5:15"):
        load_spec(write_spec(tmp_path, ok_scenes(100)), tmp_path)
