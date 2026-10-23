import wave
from pathlib import Path

import pytest

from bityodha import tts


def test_apply_pronunciations_whole_word_only():
    out = tts.apply_pronunciations("a dict and dicts", {"dict": "dictionary"})
    assert out == "a dictionary and dicts"


def test_ensure_voice_reuses_existing_files(tmp_path, monkeypatch):
    (tmp_path / "en_US-lessac-medium.onnx").write_bytes(b"x")
    (tmp_path / "en_US-lessac-medium.onnx.json").write_text("{}")

    def boom(*a, **k):
        raise AssertionError("must not download")

    monkeypatch.setattr(tts, "_download", boom)
    assert tts.ensure_voice(tmp_path) == tmp_path / "en_US-lessac-medium.onnx"


def test_ensure_voice_network_failure_raises_tts_error(tmp_path, monkeypatch):
    def fail(url, dest):
        raise OSError("no network")

    monkeypatch.setattr(tts, "_download", fail)
    with pytest.raises(tts.TtsError, match="download"):
        tts.ensure_voice(tmp_path)
    assert not list(tmp_path.glob("*.onnx"))


def test_synthesize_writes_wav_and_returns_duration(tmp_path):
    voices = Path(__file__).resolve().parent.parent / "voices"
    try:
        voice = tts.ensure_voice(voices)
    except tts.TtsError:
        pytest.skip("voice model unavailable")
    out = tmp_path / "a.wav"
    seconds = tts.synthesize("Hello from BitYodha.", voice, out)
    with wave.open(str(out)) as w:
        real = w.getnframes() / w.getframerate()
    assert seconds == pytest.approx(real)
    assert 0.5 < seconds < 6
