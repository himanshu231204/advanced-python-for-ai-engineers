# Study site (`docs/`)

This folder is the **study website** for *Advanced Python for AI Engineers* — a
presentation layer over the repository, not new learning content. All lesson
material still lives in the numbered module folders and the top-level reference
docs; this site simply renders them in a fast, searchable, dark-themed handbook.

## How it works

- [`build_site.py`](../build_site.py) (repo root) scans the real repo — module
  `README.md` files, `ROADMAP.md`, `CHEATSHEET.md`, `INTERVIEW.md`, `PATTERNS.md`,
  `GLOSSARY.md`, `PYTHON_TO_AI_ENGINEERING.md`, the `code-reading/`, `debugging/`,
  and `projects/` folders, plus their example code — and bundles everything into
  `docs/content.json`. Navigation, module titles, statuses, levels, and the
  dashboard metrics are all **derived from the files**, never hardcoded.
- `docs/index.html` + `docs/assets/` is a small single-page app that loads
  `content.json` and renders it (Markdown via marked.js, syntax highlighting via
  highlight.js, both from CDN). No build toolchain, no framework.

## Regenerate after editing content

```bash
python3 build_site.py      # rewrites docs/content.json
```

Commit `docs/content.json` together with your content changes. The GitHub Actions
workflow ([`.github/workflows/pages.yml`](../.github/workflows/pages.yml)) also
regenerates it automatically on every push to `main` before deploying.

## Preview locally

`content.json` is fetched over HTTP, so open the site through a local server
(not `file://`):

```bash
cd docs
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploy on GitHub Pages

Two supported options:

1. **GitHub Actions (recommended, keeps content fresh):** Repo → *Settings* →
   *Pages* → *Build and deployment* → **Source: GitHub Actions**. The included
   workflow rebuilds `content.json` and deploys on every push to `main`.
2. **Serve from a branch:** Repo → *Settings* → *Pages* → *Source:* **Deploy from
   a branch**, choose `main` / **`/docs`**. In this mode remember to run
   `python3 build_site.py` and commit `docs/content.json` before pushing, since
   nothing rebuilds it for you.

The site will be available at
`https://himanshu231204.github.io/advanced-python-for-ai-engineers/`.
