import pytest
from PIL import ImageChops

from bityodha.render import RenderError, render_scene, render_thumbnail
from bityodha.spec import Scene

CODE = "\n".join(f"value_{i} = {i}  # step {i}" for i in range(10))


def scene(type_: str, **kw) -> Scene:
    base = dict(id="s", type=type_, narration="n", chapter="Chapter", heading="Heading")
    base.update(kw)
    return Scene(**base)


CASES = {
    "title": (scene("title", bullets=("Module 00",)), None, None),
    "concept": (scene("concept", bullets=("one", "two")), None, None),
    "code": (scene("code", file="m/ex.py", lines=(1, 10)), CODE, None),
    "output": (scene("output", file="m/ex.py"), None, "a\nb\nc"),
    "compare": (scene("compare", bullets=("Bad | Good", "x | y")), None, None),
    "recap": (scene("recap", bullets=("one", "two")), None, None),
    "outro": (scene("outro", bullets=("Thanks",)), None, None),
}


@pytest.mark.parametrize("kind", CASES)
def test_frame_size_1080p(kind):
    s, code, out = CASES[kind]
    assert render_scene(s, code, out, 1.0).size == (1920, 1080)


def changed_pixels(a, b) -> int:
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v else 0)
    return diff.histogram()[255]


def test_progress_reveals_more_code():
    s, code, out = CASES["code"]
    blank = render_scene(s, code, out, 0.0)
    early = changed_pixels(render_scene(s, code, out, 0.2), blank)
    late = changed_pixels(render_scene(s, code, out, 0.9), blank)  # both frames carry the same highlight bar
    assert late > early


def test_overlong_code_line_raises_render_error():
    s, _, out = CASES["code"]
    with pytest.raises(RenderError, match="wider|fit"):
        render_scene(s, "x = '" + "a" * 300 + "'", out, 1.0)


def test_too_many_code_lines_raises_render_error():
    s, _, out = CASES["code"]
    with pytest.raises(RenderError):
        render_scene(s, "\n".join("x = 1" for _ in range(60)), out, 1.0)


def test_prose_wraps_instead_of_raising():
    long_bullet = " ".join(["wrapping"] * 40)
    render_scene(scene("concept", bullets=(long_bullet,)), None, None, 1.0)


def test_unbreakable_word_raises_render_error():
    with pytest.raises(RenderError):
        render_scene(scene("concept", bullets=("a" * 200,)), None, None, 1.0)


def test_thumbnail_size_1280x720():
    assert render_thumbnail("A hook title for the video", "MODULE 00").size == (1280, 720)
