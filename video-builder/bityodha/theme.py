"""BitYodha visual identity: colors, sizes and fonts."""
from typing import Literal

from PIL import ImageFont

WIDTH = 1920
HEIGHT = 1080
FPS = 30

BG = "#171726"
CODE_BG = "#0f0f1a"
ACCENT = "#f6b73c"
TEXT = "#f4f1ea"
MUTED = "#9a9bb5"
RED = "#ff0033"

_FONT_FILES = {
    "text": "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
    "bold": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
}


class FontError(RuntimeError):
    pass


def font(kind: Literal["text", "bold", "mono"], size: int) -> ImageFont.FreeTypeFont:
    path = _FONT_FILES[kind]
    try:
        return ImageFont.truetype(path, size)
    except OSError as exc:
        raise FontError(
            f"font file not found: {path} (on Debian/Ubuntu: apt install fonts-inter fonts-dejavu-core)"
        ) from exc
