# Module Videos for BitYodha — Design

**Date:** 2026-10-22
**Status:** Awaiting spec review
**First deliverable:** Module 00 (`00-python-foundation-review`)

## 1. Goal

Turn each numbered module (00–28) of this repository into one YouTube video for the
**Bit Yodha** channel (https://www.youtube.com/@BitYodha), built fully automatically as an
MP4 from the module's own lessons and runnable examples.

Modules are built **one at a time**, finishing one to a verified MP4 before starting the
next (per `CLAUDE.md`). This spec covers the shared pipeline and module 00.

### Success criteria

- Final MP4 duration is **between 5:15 and 9:45** (target 7–8 min). The build fails
  outside that range, so a video can never violate the 5–10 minute requirement.
- 1920×1080, H.264/AAC, plays in YouTube without re-encoding issues.
- Narration is English, synthetic, and clearly intelligible.
- Every code snippet on screen comes from the module's real files; every shown output is
  produced by actually running that code.
- Per module: `video.mp4`, `chapters.txt`, `metadata.md` (title, description, tags),
  `thumbnail.png`.

### Constraints and honest limits

- Offline neural TTS (Piper) is clear but synthetic; it will not match a human voiceover.
- Nothing is uploaded to YouTube. The user uploads the MP4 using the supplied metadata.
- No background music by default (licensing).
- Built MP4s are git-ignored and delivered to the user directly; only sources are committed.

## 2. Channel context (from the channel page)

- Channel "Bit Yodha", by Himanshu Kumar: AI projects, agents and RAG, ML, dev tools, DSA.
- Tagline: "Learn in public. Build real projects. Share everything."
- Existing videos are English, about 6–10 minutes, with hook-style titles and trailing
  hashtags (#ai etc.).
- Visual cues from the avatar: dark navy, warm amber accent, a crown motif,
  "Build · Learn · Ship · Repeat". The avatar itself is not used in videos.

## 3. Layout

```text
video-builder/
  README.md                  how to build a module video
  requirements.txt           pillow, pygments, pyyaml, piper-tts, pytest
  bityodha/                  pipeline package
    spec.py                  load/validate scene specs
    theme.py                 colors, fonts, wordmark
    render.py                scene -> PNG frames (Pillow + Pygments)
    runcode.py               run example code, capture real output
    tts.py                   Piper narration -> WAV per scene
    assemble.py              ffmpeg: scenes -> MP4, chapters
    metadata.py              title/description/tags/chapters files
    build.py                 CLI: python -m bityodha.build <module>
  modules/
    00-python-foundation-review/
      scenes.yaml            the scene spec for module 00
  tests/                     pytest for spec validation, timing, duration guard
  .gitignore                 out/, voices/ (downloaded models)
```

Output goes to `video-builder/out/<module>/` (ignored).

## 4. Scene spec

`scenes.yaml` holds module metadata plus an ordered list of scenes.

```yaml
module: 00-python-foundation-review
title: "Python Basics Every AI Engineer Gets Wrong (Before You Touch LLMs)"
hashtags: [ai, python, aiengineer]
scenes:
  - id: hook
    type: title            # title | concept | code | output | compare | recap | outro
    chapter: "Why this matters"
    heading: "..."
    bullets: ["..."]
    narration: "..."
  - id: dedup
    type: code
    file: 00-python-foundation-review/examples/core_data_structures.py
    lines: [12, 24]        # slice of a real repo file
    run: true              # also run the file and show its real output
    narration: "..."
```

Validation rejects: missing narration, unknown scene type, `lines` outside the file,
unknown files, and any narration word count that would put the estimated total outside the
target range (a pre-TTS estimate at about 150 words per minute).

## 5. Rendering

- 1920×1080 PNG per scene (animated reveals are produced as a short list of frames).
- Theme: navy background, amber accent, off-white text, Inter for text and DejaVu Sans
  Mono for code, a text wordmark "BitYodha" with a crown glyph drawn in Pillow.
- Code scenes: Pygments tokens drawn with Pillow; highlighted line ranges; lines revealed
  progressively across the scene's duration.
- Output scenes: terminal-style panel showing the captured real output.
- Intro card and an outro card carrying "Build · Learn · Ship · Repeat", the repo name and
  a subscribe prompt.
- Frames are checked for text overflow at render time; overflow is a build error.

## 6. Audio

- Piper TTS with one English voice downloaded from Hugging Face on first build.
- One WAV per scene; scene duration = audio length + 0.4 s pad.
- Narration is sanitized for speech (for example `dict` spoken as "dict", symbols spelled
  out) via a small per-module pronunciation map in the spec.

## 7. Assembly and outputs

- ffmpeg builds each scene clip from its frames and audio, then concatenates to
  `video.mp4` (1080p, 30 fps, H.264 yuv420p, AAC).
- `chapters.txt` is written in YouTube format (`0:00 Title` lines, starting at 0:00 with
  at least three chapters of 10 s or more).
- `metadata.md` has a hook-style title, a description (what you learn, chapters, repo
  link, the tagline, hashtags) and tags.
- `thumbnail.png` (1280×720): bold hook text, module number, wordmark.

## 8. Module 00 content plan (about 7.5 min)

Condensed to what matters for AI work; basic syntax is skipped.

| # | Chapter | Focus | Source |
|---|---------|-------|--------|
| 1 | Why this matters | Why shaky fundamentals break LLM code | README |
| 2 | Data structures | Ordered dedup of retrieved chunks with set plus list; tuple keys; dict dispatch | `examples/core_data_structures.py` |
| 3 | Control flow and comprehensions | Comprehensions as filters/transforms; generator vs list in memory | `examples/comprehensions.py` |
| 4 | Functions and scope | Mutable default argument bug, aliasing, late binding | `examples/scope_and_references.py` |
| 5 | Exceptions | Specific except clauses, `raise from`, never a bare `except` | `examples/exception_basics.py` |
| 6 | Modules and imports | Packages, circular imports, why it matters for project layout | `modules-imports.md` |
| 7 | Recap and next | Summary, bridge to module 01 | README |

## 9. Error handling

- Missing Piper voice: download it; if the network fails, stop with a clear error.
- Any example that fails to run: build stops (the repo rule is that examples execute).
- Duration outside 5:15–9:45: build stops and reports the actual and allowed range.
- ffmpeg failures surface stderr.

## 10. Testing and verification

- pytest unit tests for spec validation, line-range slicing, duration estimator, chapter
  formatting, and the duration guard (using fake durations).
- A smoke test builds a short 3-scene sample end to end when Piper is available.
- Module 00 acceptance: ffprobe confirms duration, resolution and codecs; sampled frames
  from each chapter are viewed for legibility; the example files are executed.

## 11. Out of scope

- Uploading to YouTube, thumbnails A/B testing, subtitle burning, music, human voice.
- Modules 01–28 (they reuse this pipeline later, one at a time).
