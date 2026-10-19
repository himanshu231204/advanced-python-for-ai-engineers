"""Run from any cwd; load only this exercise's fixed module."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


def load_fixed() -> ModuleType:
    spec = importlib.util.spec_from_file_location("retrieval_boundary_fixed", Path(__file__).with_name("fixed.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixed = load_fixed()


def test_normalizes_adapter_score() -> None:
    assert fixed.rank_record({"score": "0.82"}) == "keep"
    assert fixed.rank_record({"score": 0.2}) == "discard"


@pytest.mark.parametrize("record", [{}, {"score": "unknown"}, {"score": True}, {"score": None}, {"score": "nan"}, {"score": 1.5}])
def test_rejects_invalid_score(record: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="score"):
        fixed.rank_record(record)


def test_normal_script_terminates_without_input() -> None:
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("fixed.py"))], input="", capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "keep"
    assert "score_type=str" in result.stderr
