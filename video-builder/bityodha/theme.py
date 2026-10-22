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


def font(kind: Literal["text", "bold", "mono"], size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_FONT_FILES[kind], size)
