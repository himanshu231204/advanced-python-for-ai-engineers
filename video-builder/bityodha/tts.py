"""Offline narration with Piper TTS."""
import re
import urllib.request
import wave
from pathlib import Path

VOICE_NAME = "en_US-lessac-medium"
VOICE_BASE_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/"
)


class TtsError(RuntimeError):
    pass


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as resp:
        dest.write_bytes(resp.read())


def ensure_voice(voices_dir: Path) -> Path:
    voices_dir.mkdir(parents=True, exist_ok=True)
    model = voices_dir / f"{VOICE_NAME}.onnx"
    config = voices_dir / f"{VOICE_NAME}.onnx.json"
    for dest in (model, config):
        if dest.exists():
            continue
        tmp = dest.with_name(dest.name + ".part")
        try:
            _download(VOICE_BASE_URL + dest.name, tmp)
            tmp.rename(dest)
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            raise TtsError(f"could not download {dest.name}: {exc}") from exc
    return model


def apply_pronunciations(text: str, mapping: dict[str, str]) -> str:
    for word, spoken in mapping.items():
        text = re.sub(rf"\b{re.escape(word)}\b", spoken, text)
    return text


_voice_cache: dict[Path, object] = {}


def synthesize(text: str, voice_path: Path, out_wav: Path) -> float:
    from piper import PiperVoice

    voice = _voice_cache.get(voice_path)
    if voice is None:
        voice = _voice_cache[voice_path] = PiperVoice.load(voice_path)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    with wave.open(str(out_wav)) as w:
        return w.getnframes() / w.getframerate()
