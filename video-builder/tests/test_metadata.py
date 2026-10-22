from bityodha.metadata import REPO_URL, write_metadata
from bityodha.spec import ModuleSpec, Scene


def test_metadata_contains_chapters_repo_tagline_and_hashtags(tmp_path):
    spec = ModuleSpec(
        module="00-python-foundation-review",
        title="Python Basics Every AI Engineer Gets Wrong",
        hashtags=["ai", "python"],
        scenes=[Scene(id="a", type="title", narration="n")],
    )
    path = write_metadata(spec, "0:00 Intro\n0:30 Data\n1:10 Wrap", tmp_path)
    text = path.read_text()
    assert "Python Basics Every AI Engineer Gets Wrong" in text
    assert "0:30 Data" in text
    assert REPO_URL in text
    assert "Learn in public. Build real projects. Share everything." in text
    assert "#ai #python" in text
    assert "Module 00" in text
    assert "Tags:" in text
