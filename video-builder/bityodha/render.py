"""Render scenes (and the thumbnail) to Pillow images."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

from . import theme
from .spec import Scene
from .theme import HEIGHT, WIDTH, font

MARGIN = 80
CONTENT_BOTTOM = HEIGHT - 70
TAGLINE = "Learn in public. Build real projects. Share everything."
SLOGAN = "Build · Learn · Ship · Repeat"
CODE_SIZES = (34, 32, 30, 28, 26, 24, 22)


class RenderError(RuntimeError):
    pass


# ---------------------------------------------------------------- helpers

def _wrap(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        if fnt.getlength(word) > max_w:
            raise RenderError(f"word {word[:20]!r}... is wider than {max_w}px and cannot wrap")
        trial = f"{current} {word}".strip()
        if fnt.getlength(trial) <= max_w:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_lines(draw, lines, fnt, x, y, color, line_h, bottom=CONTENT_BOTTOM, center_w=None) -> int:
    for line in lines:
        if y + line_h > bottom:
            raise RenderError(f"text does not fit: runs past y={bottom}")
        lx = x if center_w is None else x + (center_w - fnt.getlength(line)) / 2
        draw.text((lx, y), line, font=fnt, fill=color)
        y += line_h
    return y


def _draw_wordmark(draw, x: int, y: int, scale: float = 1.0) -> int:
    s = scale
    crown = [(0, 22), (0, 4), (9, 14), (18, 0), (27, 14), (36, 4), (36, 22)]
    draw.polygon([(x + px * s, y + 6 * s + py * s) for px, py in crown], fill=theme.ACCENT)
    f = font("bold", int(34 * s))
    tx = x + 52 * s
    draw.text((tx, y), "Bit", font=f, fill=theme.TEXT)
    draw.text((tx + f.getlength("Bit"), y), "Yodha", font=f, fill=theme.ACCENT)
    return int(tx + f.getlength("BitYodha"))


def _chrome(draw, scene: Scene) -> None:
    _draw_wordmark(draw, MARGIN, 36)
    if scene.chapter:
        f = font("text", 28)
        draw.text((WIDTH - MARGIN - f.getlength(scene.chapter.upper()), 44),
                  scene.chapter.upper(), font=f, fill=theme.MUTED)


def _heading(draw, text: str | None, y: int = 120, size: int = 60) -> int:
    if not text:
        return y
    f = font("bold", size)
    y = _draw_lines(draw, _wrap(text, f, WIDTH - 2 * MARGIN), f, MARGIN, y, theme.TEXT, int(size * 1.2))
    draw.rectangle((MARGIN, y + 6, MARGIN + 140, y + 12), fill=theme.ACCENT)
    return y + 40


# ------------------------------------------------------------ code / output

def _color(ttype) -> str:
    if ttype in Token.Comment:
        return "#6b6f8f"
    if ttype in Token.Keyword:
        return "#c792ea"
    if ttype in Token.String:
        return "#c3e88d"
    if ttype in Token.Number:
        return "#f78c6c"
    if ttype in Token.Name.Function or ttype in Token.Name.Class:
        return "#82aaff"
    if ttype in Token.Name.Builtin:
        return "#ffcb6b"
    if ttype in Token.Operator:
        return "#89ddff"
    return theme.TEXT


def _highlight(code: str) -> list[list[tuple[str, str]]]:
    lines: list[list[tuple[str, str]]] = [[]]
    for ttype, value in lex(code, PythonLexer(stripnl=False, ensurenl=False)):
        for i, part in enumerate(value.split("\n")):
            if i:
                lines.append([])
            if part:
                lines[-1].append((part, _color(ttype)))
    return lines[: len(code.split("\n"))]


def _panel(img, draw, top, title, lines, first_no, progress) -> None:
    bottom = CONTENT_BOTTOM + 30
    draw.rounded_rectangle((MARGIN, top, WIDTH - MARGIN, bottom), radius=18, fill=theme.CODE_BG)
    draw.text((MARGIN + 30, top + 16), title, font=font("mono", 24), fill=theme.MUTED)
    gutter = 80 if first_no is not None else 0
    code_top = top + 70
    avail_h = bottom - 24 - code_top
    avail_w = WIDTH - 2 * MARGIN - 60 - gutter
    for size in CODE_SIZES:
        fnt = font("mono", size)
        line_h = int(size * 1.45)
        widest = max((fnt.getlength("".join(t for t, _ in ln)) for ln in lines), default=0)
        if widest <= avail_w and len(lines) * line_h <= avail_h:
            break
    else:
        raise RenderError(
            f"code does not fit: {len(lines)} lines, widest line wider than the panel "
            f"(max {avail_w}px wide, {avail_h}px tall at {CODE_SIZES[-1]}px font)"
        )
    n = len(lines)
    visible = 0 if progress <= 0 else min(n, max(1, math.ceil(progress * n)))
    for i in range(visible):
        y = code_top + i * line_h
        if i == visible - 1 and visible < n:
            draw.rectangle((MARGIN + 12, y - 2, WIDTH - MARGIN - 12, y + line_h - 4), fill="#1f1f36")
        if first_no is not None:
            num = str(first_no + i)
            draw.text((MARGIN + 30 + gutter - 24 - fnt.getlength(num), y), num, font=fnt, fill="#4d4f70")
        x = MARGIN + 30 + gutter
        for text, color in lines[i]:
            draw.text((x, y), text, font=fnt, fill=color)
            x += fnt.getlength(text)


# ------------------------------------------------------------------ scenes

def _bullets(draw, bullets, y, numbered=False, size=44) -> int:
    f = font("text", size)
    line_h = int(size * 1.35)
    for i, b in enumerate(bullets, 1):
        marker = f"{i}." if numbered else "•"
        draw.text((MARGIN, y), marker, font=font("bold", size), fill=theme.ACCENT)
        y = _draw_lines(draw, _wrap(b, f, WIDTH - 2 * MARGIN - 90), f, MARGIN + 80, y, theme.TEXT, line_h)
        y += 22
    return y


def _compare(draw, bullets, y) -> None:
    rows = [[c.strip() for c in b.split("|")] for b in bullets]
    if any(len(r) != 2 for r in rows):
        raise RenderError("compare bullets must look like 'left | right'")
    col_w = (WIDTH - 2 * MARGIN - 60) // 2
    xs = (MARGIN, MARGIN + col_w + 60)
    head = font("bold", 40)
    for x, text in zip(xs, rows[0]):
        draw.text((x, y), text, font=head, fill=theme.ACCENT)
    y += 70
    body = font("text", 36)
    for row in rows[1:]:
        wrapped = [_wrap(c, body, col_w) for c in row]
        for x, lines in zip(xs, wrapped):
            _draw_lines(draw, lines, body, x, y, theme.TEXT, 48)
        y += max(len(w) for w in wrapped) * 48 + 30


def render_scene(scene: Scene, code: str | None, output: str | None, progress: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), theme.BG)
    draw = ImageDraw.Draw(img)
    kind = scene.type

    if kind in ("title", "outro"):
        _draw_wordmark(draw, MARGIN, 36)
        f = font("bold", 104)
        lines = _wrap(scene.heading or "", f, WIDTH - 2 * MARGIN)
        y = 330 - (len(lines) - 1) * 60
        y = _draw_lines(draw, lines, f, MARGIN, y, theme.TEXT, 120, center_w=WIDTH - 2 * MARGIN)
        draw.rectangle((WIDTH // 2 - 90, y + 10, WIDTH // 2 + 90, y + 18), fill=theme.ACCENT)
        sub = font("text", 42)
        y += 50
        for b in scene.bullets:
            y = _draw_lines(draw, _wrap(b, sub, WIDTH - 2 * MARGIN), sub, MARGIN, y, theme.MUTED, 58,
                            center_w=WIDTH - 2 * MARGIN)
        if kind == "outro":
            f2 = font("bold", 56)
            draw.text(((WIDTH - f2.getlength(SLOGAN)) / 2, 800), SLOGAN, font=f2, fill=theme.ACCENT)
            f3 = font("text", 32)
            draw.text(((WIDTH - f3.getlength(TAGLINE)) / 2, 890), TAGLINE, font=f3, fill=theme.MUTED)
        return img

    _chrome(draw, scene)
    top = _heading(draw, scene.heading)
    if kind == "concept":
        _bullets(draw, scene.bullets, top)
    elif kind == "recap":
        _bullets(draw, scene.bullets, top, numbered=True)
    elif kind == "compare":
        _compare(draw, scene.bullets, top)
    elif kind == "code":
        if code is None:
            raise RenderError(f"scene {scene.id}: code scene needs code")
        name = Path(scene.file).name if scene.file else "snippet.py"
        first = scene.lines[0] if scene.lines else 1
        last = scene.lines[1] if scene.lines else first + len(code.splitlines()) - 1
        _panel(img, draw, top, f"{name}  ·  lines {first}-{last}", _highlight(code), first, progress)
    elif kind == "output":
        if output is None:
            raise RenderError(f"scene {scene.id}: output scene needs output")
        name = Path(scene.file).name if scene.file else "script.py"
        lines = [[(ln, theme.TEXT)] for ln in output.split("\n")]
        _panel(img, draw, top, f"$ python {name}", lines, None, progress)
    return img


def render_thumbnail(title: str, module_label: str) -> Image.Image:
    img = Image.new("RGB", (1280, 720), theme.BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 24, 720), fill=theme.ACCENT)
    pill = font("bold", 34)
    w = int(pill.getlength(module_label)) + 50
    draw.rounded_rectangle((80, 70, 80 + w, 134), radius=32, fill=theme.ACCENT)
    draw.text((105, 79), module_label, font=pill, fill=theme.BG)
    f = font("bold", 92)
    lines = _wrap(title, f, 1280 - 160)
    if len(lines) > 4:
        f = font("bold", 72)
        lines = _wrap(title, f, 1280 - 160)
    _draw_lines(draw, lines, f, 80, 190, theme.TEXT, int(f.size * 1.18), bottom=640)
    _draw_wordmark(draw, 80, 636, 1.0)
    return img
