import pytest

from bityodha.runcode import RunError, run_example, slice_lines


def test_slice_lines_inclusive(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("one\ntwo\nthree\nfour\n")
    assert slice_lines(f, (2, 3)) == "two\nthree"


def test_run_example_returns_stdout(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("print('hi')\n")
    assert run_example(f) == "hi"


def test_run_example_nonzero_raises_with_filename(tmp_path):
    f = tmp_path / "boom.py"
    f.write_text("raise SystemExit(3)\n")
    with pytest.raises(RunError, match="boom.py"):
        run_example(f)


def test_run_example_empty_output_raises(tmp_path):
    f = tmp_path / "quiet.py"
    f.write_text("x = 1\n")
    with pytest.raises(RunError, match="quiet.py"):
        run_example(f)


def test_run_example_timeout_raises(tmp_path):
    f = tmp_path / "slow.py"
    f.write_text("import time\ntime.sleep(5)\nprint('x')\n")
    with pytest.raises(RunError, match="slow.py"):
        run_example(f, timeout=0.5)
