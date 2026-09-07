#!/usr/bin/env python3
"""Generate docs/content.json for the study website.

The website (docs/) is a *presentation layer* over this repository. This script
scans the real repo — module READMEs, top-level reference docs, code-reading and
debugging exercises, projects, and their example code — and bundles everything
into a single static JSON file the SPA loads. Nothing about the curriculum is
hardcoded here: titles, statuses, levels, and the navigation tree are all derived
from the files that actually exist.

Run it whenever content changes:

    python3 build_site.py

Then commit docs/content.json alongside your content edits.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"

# File extension -> highlight.js language hint used when embedding code files.
LANG_BY_EXT = {
    ".py": "python",
    ".md": "markdown",
    ".txt": "text",
    ".toml": "toml",
    ".cfg": "ini",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "bash",
}

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
STATUS_RE = re.compile(r"\*\*Status:\*\*\s*([^\|\n]+)")
LEVEL_RE = re.compile(r"\*\*Level:\*\*\s*([^\|\n]+)")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def first_h1(md: str, fallback: str) -> str:
    m = H1_RE.search(md)
    return m.group(1).strip() if m else fallback


def parse_status(md: str) -> str:
    m = STATUS_RE.search(md)
    if not m:
        return ""
    raw = m.group(1).strip()
    # Normalize to a simple token the UI can style.
    if "Written" in raw:
        return "Written"
    if "Planned" in raw:
        return "Planned"
    return raw


def parse_level(md: str) -> str:
    m = LEVEL_RE.search(md)
    return m.group(1).strip() if m else ""


def collect_code(folder: Path) -> list[dict]:
    """Embed small source files found under a module/project folder."""
    files: list[dict] = []
    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        if p.name == "README.md":
            continue
        ext = p.suffix.lower()
        if ext not in LANG_BY_EXT:
            continue
        try:
            text = read(p)
        except (UnicodeDecodeError, OSError):
            continue
        if len(text) > 60_000:  # skip anything unexpectedly huge
            continue
        files.append(
            {
                "name": str(p.relative_to(folder)),
                "language": LANG_BY_EXT[ext],
                "code": text,
            }
        )
    return files


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    docs: dict[str, dict] = {}
    nav: list[dict] = []

    def add_doc(doc_id: str, **fields) -> None:
        docs[doc_id] = fields

    # ---- Home / Dashboard (synthetic, rendered by the SPA) ----
    nav.append({"id": "home", "title": "Home", "icon": "home", "type": "page"})

    # ---- Learning Roadmap ----
    roadmap = ROOT / "ROADMAP.md"
    if roadmap.exists():
        md = read(roadmap)
        add_doc("roadmap", title="Learning Roadmap", markdown=md, source=rel(roadmap))
        nav.append({"id": "roadmap", "title": "Learning Roadmap", "icon": "map", "type": "doc"})

    # ---- Modules 00–28 ----
    module_dirs = sorted(
        [p for p in ROOT.iterdir() if p.is_dir() and re.match(r"^\d\d-", p.name)]
    )
    module_children: list[dict] = []
    module_order: list[str] = []
    for d in module_dirs:
        readme = d / "README.md"
        if not readme.exists():
            continue
        md = read(readme)
        num = d.name[:2]
        title = first_h1(md, d.name)
        status = parse_status(md)
        level = parse_level(md)
        doc_id = d.name
        module_order.append(doc_id)
        add_doc(
            doc_id,
            title=title,
            markdown=md,
            status=status,
            level=level,
            number=num,
            folder=d.name,
            source=rel(readme),
            code=collect_code(d),
            kind="module",
        )
        module_children.append(
            {
                "id": doc_id,
                "title": title,
                "number": num,
                "status": status,
                "level": level,
                "type": "doc",
            }
        )
    # prev/next links across modules
    for i, doc_id in enumerate(module_order):
        docs[doc_id]["prev"] = module_order[i - 1] if i > 0 else None
        docs[doc_id]["next"] = module_order[i + 1] if i < len(module_order) - 1 else None

    nav.append(
        {
            "id": "modules",
            "title": "Modules",
            "icon": "layers",
            "type": "group",
            "children": module_children,
        }
    )

    # ---- Code Reading ----
    cr = ROOT / "code-reading"
    if cr.exists():
        children = []
        overview = cr / "README.md"
        if overview.exists():
            add_doc("code-reading", title=first_h1(read(overview), "Code Reading"),
                    markdown=read(overview), source=rel(overview), kind="practice")
            children.append({"id": "code-reading", "title": "Overview", "type": "doc"})
        for ex in sorted((cr / "exercises").glob("*.md")):
            md = read(ex)
            doc_id = f"code-reading/{ex.stem}"
            add_doc(doc_id, title=first_h1(md, ex.stem), markdown=md, source=rel(ex), kind="practice")
            children.append({"id": doc_id, "title": first_h1(md, ex.stem), "type": "doc"})
        nav.append({"id": "code-reading", "title": "Code Reading", "icon": "eye",
                    "type": "group", "children": children})

    # ---- Debugging ----
    dbg = ROOT / "debugging"
    if dbg.exists():
        children = []
        overview = dbg / "README.md"
        if overview.exists():
            add_doc("debugging", title=first_h1(read(overview), "Debugging"),
                    markdown=read(overview), source=rel(overview), kind="practice")
            children.append({"id": "debugging", "title": "Overview", "type": "doc"})
        for ex in sorted((dbg / "exercises").iterdir()):
            if not ex.is_dir():
                continue
            readme = ex / "README.md"
            md = read(readme) if readme.exists() else f"# {ex.name}\n"
            doc_id = f"debugging/{ex.name}"
            add_doc(doc_id, title=first_h1(md, ex.name), markdown=md,
                    source=rel(ex), code=collect_code(ex), kind="practice")
            children.append({"id": doc_id, "title": first_h1(md, ex.name), "type": "doc"})
        nav.append({"id": "debugging", "title": "Debugging", "icon": "bug",
                    "type": "group", "children": children})

    # ---- Projects ----
    proj = ROOT / "projects"
    if proj.exists():
        children = []
        overview = proj / "README.md"
        if overview.exists():
            add_doc("projects", title=first_h1(read(overview), "Projects"),
                    markdown=read(overview), source=rel(overview), kind="project")
            children.append({"id": "projects", "title": "Overview", "type": "doc"})
        for pd in sorted([p for p in proj.iterdir() if p.is_dir()]):
            readme = pd / "README.md"
            if not readme.exists():
                continue
            md = read(readme)
            doc_id = f"projects/{pd.name}"
            add_doc(doc_id, title=first_h1(md, pd.name), markdown=md,
                    source=rel(readme), code=collect_code(pd), kind="project")
            children.append({"id": doc_id, "title": first_h1(md, pd.name), "type": "doc"})
        nav.append({"id": "projects", "title": "Projects", "icon": "box",
                    "type": "group", "children": children})

    # ---- Python Builtins for AI Engineers ----
    builtins_dir = ROOT / "python-builtins-for-ai-engineers"
    if builtins_dir.exists():
        children = []
        overview = builtins_dir / "README.md"
        if overview.exists():
            add_doc("builtins", title=first_h1(read(overview), "Python Builtins for AI Engineers"),
                    markdown=read(overview), source=rel(overview), kind="reference")
            children.append({"id": "builtins", "title": "Overview", "type": "doc"})
        for md_file in sorted(builtins_dir.glob("[0-9][0-9]-*.md")):
            md = read(md_file)
            doc_id = f"builtins/{md_file.stem}"
            add_doc(doc_id, title=first_h1(md, md_file.stem), markdown=md,
                    source=rel(md_file), kind="reference")
            children.append({"id": doc_id, "title": first_h1(md, md_file.stem), "type": "doc"})
        nav.append({"id": "builtins", "title": "Python Builtins", "icon": "library",
                    "type": "group", "children": children})

    # ---- Python Keywords for AI Engineers ----
    keywords_dir = ROOT / "python-keywords-for-ai-engineers"
    if keywords_dir.exists():
        children = []
        overview = keywords_dir / "README.md"
        if overview.exists():
            add_doc("keywords", title=first_h1(read(overview), "Python Keywords for AI Engineers"),
                    markdown=read(overview), source=rel(overview), kind="reference")
            children.append({"id": "keywords", "title": "Overview", "type": "doc"})
        for md_file in sorted(keywords_dir.glob("[0-9][0-9]-*.md")):
            md = read(md_file)
            doc_id = f"keywords/{md_file.stem}"
            add_doc(doc_id, title=first_h1(md, md_file.stem), markdown=md,
                    source=rel(md_file), kind="reference")
            children.append({"id": doc_id, "title": first_h1(md, md_file.stem), "type": "doc"})
        nav.append({"id": "keywords", "title": "Python Keywords", "icon": "key",
                    "type": "group", "children": children})

    # ---- Single-file reference docs ----
    references = [
        ("cheatsheet", "CHEATSHEET.md", "Cheatsheet", "list"),
        ("interview", "INTERVIEW.md", "Interview Questions", "mic"),
        ("patterns", "PATTERNS.md", "Patterns", "puzzle"),
        ("glossary", "GLOSSARY.md", "Glossary", "book"),
        ("python-to-ai", "PYTHON_TO_AI_ENGINEERING.md", "Python → AI Engineering", "cpu"),
    ]
    for doc_id, fname, title, icon in references:
        f = ROOT / fname
        if f.exists():
            add_doc(doc_id, title=title, markdown=read(f), source=rel(f))
            nav.append({"id": doc_id, "title": title, "icon": icon, "type": "doc"})

    # ---- Dashboard metrics (derived, never hardcoded) ----
    written = sum(1 for m in module_order if docs[m]["status"] == "Written")
    total = len(module_order)
    levels: dict[str, int] = {}
    for m in module_order:
        lvl = docs[m]["level"]
        levels[lvl] = levels.get(lvl, 0) + 1

    meta = {
        "repo": "himanshu231204/advanced-python-for-ai-engineers",
        "repo_url": "https://github.com/himanshu231204/advanced-python-for-ai-engineers",
        "title": "Advanced Python for AI Engineers",
        "modules_written": written,
        "modules_total": total,
        "levels": levels,
        "module_order": module_order,
    }

    payload = {"meta": meta, "nav": nav, "docs": docs}
    DOCS.mkdir(exist_ok=True)
    out = DOCS / "content.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=None), encoding="utf-8")
    size_kb = out.stat().st_size / 1024
    print(f"Wrote {out.relative_to(ROOT)} — {len(docs)} docs, "
          f"{written}/{total} modules written, {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
