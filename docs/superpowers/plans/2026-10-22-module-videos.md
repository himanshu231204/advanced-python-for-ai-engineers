# Module Videos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pipeline that turns a module's scene spec into a 1080p MP4 with narration, chapters, YouTube metadata and a thumbnail, then use it to produce the module 00 video for the BitYodha channel.

**Architecture:** A `video-builder/bityodha` Python package. A YAML scene spec is validated, each scene is rendered to PNG frames with Pillow, narrated with offline Piper TTS, and assembled with ffmpeg. Code shown on screen is sliced from real repo files and its output captured by running them.

**Tech Stack:** Python 3.12+, Pillow, Pygments, PyYAML, piper-tts, ffmpeg/ffprobe (system), pytest.

**Spec:** `docs/superpowers/specs/2026-10-22-module-videos-design.md`

## Global Constraints

- Final MP4 duration must be within **5:15 and 9:45** (315–585 s); the build fails otherwise.
- Output: 1920×1080, 30 fps, H.264 (yuv420p) video, AAC audio. Thumbnail 1280×720.
- Narration is English, offline Piper TTS, one voice (`en_US-lessac-medium` from `rhasspy/piper-voices` on Hugging Face), about 150 words per minute for estimation.
- Theme: navy background, amber accent, off-white text; Inter (text) and DejaVu Sans Mono (code); text wordmark "BitYodha" with a crown glyph; outro line "Build · Learn · Ship · Repeat"; channel tagline "Learn in public. Build real projects. Share everything."
- No background music. No avatar image. No upload to YouTube.
- Built artifacts go to `video-builder/out/<module>/` and the downloaded voice to `video-builder/voices/`; both are git-ignored.
- Per `CLAUDE.md`: own `requirements.txt` inside `video-builder/`; run its pytest suite from that directory only; every on-screen example must actually run; one module finished before the next.
- Python 3.12+ syntax.

## Review Focus

- A scene whose `lines` range is past the end of the file, reversed, or from a file that does not exist: validation error naming the scene.
- A code line wider than the frame: render error instead of silently clipped text.
- An example that exits non-zero or prints nothing: build stops, naming the file.
- Total duration just under 5:15 or just over 9:45 (boundaries inclusive 315 and 585): guard passes at the bounds and fails one second outside.
- Re-running a build with existing `out/` files or an existing voice model: reuses the voice, overwrites outputs, no stale scenes from a previous longer spec.

---

### Task 1: Package scaffold, theme and spec loader

**Files:**
- Create: `video-builder/requirements.txt`, `video-builder/.gitignore`, `video-builder/README.md`
- Create: `video-builder/bityodha/__init__.py`, `video-builder/bityodha/theme.py`, `video-builder/bityodha/spec.py`
- Test: `video-builder/tests/test_spec.py`

**Interfaces:**
- Produces:
  - `theme.py`: constants `WIDTH=1920`, `HEIGHT=1080`, `FPS=30`, `BG`, `ACCENT`, `TEXT`, `MUTED`, `CODE_BG` (hex strings); `font(kind: Literal["text","bold","mono"], size: int) -> ImageFont.FreeTypeFont`.
  - `spec.py`: `@dataclass Scene(id, type, narration, chapter=None, heading=None, bullets=(), file=None, lines=None, run=False)`; `@dataclass ModuleSpec(module, title, hashtags, scenes, pronunciations)`; `load_spec(path: Path, repo_root: Path) -> ModuleSpec` raising `SpecError(str)`; `estimate_seconds(spec: ModuleSpec) -> float` (words / 150 * 60 plus 0.4 s per scene).

- [ ] **Step 1: Write failing tests** in `tests/test_spec.py`: `test_loads_valid_spec`; `test_rejects_unknown_scene_type` (error message contains the scene id); `test_rejects_lines_past_end_of_file`; `test_rejects_reversed_lines`; `test_rejects_missing_file`; `test_rejects_empty_narration`; `test_estimate_seconds_uses_150_wpm` (300 words, 1 scene ≈ 120.4 s); `test_rejects_estimate_outside_range` (spec of 100 words → `SpecError` mentioning "5:15").
- [ ] **Step 2: Run** `cd video-builder && python3 -m pytest tests/test_spec.py -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** the files above. Scene types: `title|concept|code|output|compare|recap|outro`. `lines` is a 1-indexed inclusive `[start, end]`. The estimate range check lives in `load_spec`. `requirements.txt` pins `pillow`, `pygments`, `pyyaml`, `piper-tts`, `pytest`. `.gitignore` lists `out/`, `voices/`, `__pycache__/`.
- [ ] **Step 4: Run tests.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(video-builder): scaffold package, theme and spec loader`.

### Task 2: Real code slicing and execution

**Files:**
- Create: `video-builder/bityodha/runcode.py`
- Test: `video-builder/tests/test_runcode.py`

**Interfaces:**
- Consumes: `Scene` from Task 1.
- Produces: `slice_lines(path: Path, lines: tuple[int, int]) -> str`; `run_example(path: Path, timeout: float = 30) -> str` (stdout, stripped), raising `RunError(str)` on non-zero exit, timeout, or empty stdout.

- [ ] **Step 1: Write failing tests**: `test_slice_lines_inclusive`; `test_run_example_returns_stdout` (temp script printing `hi`); `test_run_example_nonzero_raises_with_filename`; `test_run_example_empty_output_raises`; `test_run_example_timeout_raises`.
- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement** with `subprocess.run([sys.executable, "-I", str(path)], cwd=path.parent, ...)`.
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** `feat(video-builder): slice and run real example code`.

### Task 3: Scene renderer

**Files:**
- Create: `video-builder/bityodha/render.py`
- Test: `video-builder/tests/test_render.py`

**Interfaces:**
- Consumes: `theme` constants/`font`; `Scene`.
- Produces: `render_scene(scene: Scene, code: str | None, output: str | None, progress: float) -> Image.Image` (1920×1080 RGB; `progress` 0–1 reveals code lines proportionally); `render_thumbnail(title: str, module_label: str) -> Image.Image` (1280×720); raises `RenderError(str)` when any text line exceeds the usable width (frame width minus 160 px margins) after wrapping prose, and for code lines wider than the code panel.

- [ ] **Step 1: Write failing tests**: `test_frame_size_1080p` for each scene type; `test_progress_reveals_more_code` (non-background pixel count at 1.0 is greater than at 0.2); `test_overlong_code_line_raises_render_error`; `test_prose_wraps_instead_of_raising`; `test_thumbnail_size_1280x720`.
- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement** with Pillow plus Pygments token colors mapped to the theme. Draw the crown glyph with `ImageDraw.polygon` next to the "BitYodha" wordmark in a corner of every scene; the `outro` scene adds "Build · Learn · Ship · Repeat". The `output` scene draws a terminal-style panel; `compare` draws two columns of bullets.
- [ ] **Step 4: Run, expect PASS.** Also save one frame per scene type into `out/_preview/` and view them for legibility.
- [ ] **Step 5: Commit** `feat(video-builder): render scenes and thumbnail`.

### Task 4: Piper narration

**Files:**
- Create: `video-builder/bityodha/tts.py`
- Test: `video-builder/tests/test_tts.py`

**Interfaces:**
- Produces: `ensure_voice(voices_dir: Path) -> Path` (downloads `en_US-lessac-medium.onnx` and `.onnx.json` from `https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/` if absent, raising `TtsError` on failure); `apply_pronunciations(text: str, mapping: dict[str, str]) -> str` (whole-word, case-sensitive replacement); `synthesize(text: str, voice_path: Path, out_wav: Path) -> float` (returns duration in seconds).

- [ ] **Step 1: Write failing tests**: `test_apply_pronunciations_whole_word_only`; `test_ensure_voice_reuses_existing_files` (pre-created files are not re-downloaded; patch the downloader); `test_ensure_voice_network_failure_raises_tts_error`; `test_synthesize_writes_wav_and_returns_duration` (marked to skip when the voice is not present).
- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement** using `piper.PiperVoice.load(...)` and its WAV synthesis method; confirm the exact method name in the installed piper-tts 1.8.0 before coding. Read duration from the WAV header.
- [ ] **Step 4: Run, expect PASS** (after `pip install -r requirements.txt`).
- [ ] **Step 5: Commit** `feat(video-builder): offline piper narration`.

### Task 5: Assembly, chapters and duration guard

**Files:**
- Create: `video-builder/bityodha/assemble.py`
- Test: `video-builder/tests/test_assemble.py`

**Interfaces:**
- Consumes: frame renderer from Task 3 and wav files from Task 4 (as paths).
- Produces: `MIN_SECONDS=315`, `MAX_SECONDS=585`; `check_duration(total: float) -> None` raising `DurationError` whose message states the actual and allowed range; `format_chapters(chapters: list[tuple[str, float]]) -> str` (YouTube `M:SS Title` lines, first at `0:00`, requires ≥3 chapters, each ≥10 s); `build_video(scene_clips: list[SceneClip], out_mp4: Path) -> None` where `SceneClip(frames_dir: Path, fps: int, wav: Path, duration: float)`.

- [ ] **Step 1: Write failing tests**: `test_check_duration_accepts_bounds` (315 and 585 pass); `test_check_duration_rejects_314_and_586`; `test_format_chapters_starts_at_zero`; `test_format_chapters_rejects_fewer_than_three`; `test_format_chapters_rejects_chapter_under_10s`; `test_build_video_produces_mp4` (two tiny solid-color scenes with generated silence; verify with ffprobe that it is h264 and aac).
- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement** with `ffmpeg` via subprocess: per scene, loop frames at `fps` for `duration` and mux the wav; concat demuxer; `-c:v libx264 -pix_fmt yuv420p -c:a aac`. Surface stderr in errors.
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** `feat(video-builder): ffmpeg assembly, chapters, duration guard`.

### Task 6: Metadata and build CLI

**Files:**
- Create: `video-builder/bityodha/metadata.py`, `video-builder/bityodha/build.py`
- Test: `video-builder/tests/test_metadata.py`, `video-builder/tests/test_build.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `write_metadata(spec: ModuleSpec, chapters_text: str, out_dir: Path) -> Path` (writes `metadata.md` with title, description containing the chapters, repo link `https://github.com/himanshu231204/advanced-python-for-ai-engineers`, the tagline, hashtags, and a tags line); CLI `python3 -m bityodha.build <module-folder-name> [--no-tts-cache]` that writes `video.mp4`, `chapters.txt`, `metadata.md`, `thumbnail.png` to `out/<module>/`.

- [ ] **Step 1: Write failing tests**: `test_metadata_contains_chapters_repo_tagline_and_hashtags`; `test_build_clears_stale_scene_files` (pre-existing `scene_99.*` removed); `test_build_stops_when_example_fails` (names the file); `test_build_end_to_end_smoke` (three-scene sample spec built with a stubbed TTS and the duration guard patched to the sample's length; skipped if ffmpeg is missing).
- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement** the pipeline order: load spec → run examples → TTS per scene → render frames with progress per frame → assemble → duration guard on the real total → write chapters, metadata, thumbnail. Document usage in `video-builder/README.md`.
- [ ] **Step 4: Run the full suite** (`cd video-builder && python3 -m pytest -v`). Expected: all PASS.
- [ ] **Step 5: Commit** `feat(video-builder): metadata and build CLI`.

### Task 7: Module 00 scenes and verified video

**Files:**
- Create: `video-builder/modules/00-python-foundation-review/scenes.yaml`

**Interfaces:**
- Consumes: the build CLI. Scene content follows the spec's section 8 chapter table. Narration totals roughly 1,100–1,250 words. Every `code` scene points at a real `00-python-foundation-review/examples/*.py` slice; chapter 6 (modules and imports) uses a `concept` scene sourced from `modules-imports.md`; the first scene is a `title` hook and the last two are `recap` and `outro`. Title: "Python Basics Every AI Engineer Gets Wrong (Before You Touch LLMs)"; hashtags `ai`, `python`, `aiengineer`.

- [ ] **Step 1: Read** the module's README, four topic files and four examples, then write `scenes.yaml` with seven chapters covering the plan table. Narration must not claim anything the lessons do not teach.
- [ ] **Step 2: Run** `cd video-builder && python3 -m bityodha.build 00-python-foundation-review`. Expected: finishes without `SpecError`, `RunError`, `RenderError` or `DurationError`. If the guard fails, adjust narration length, not the guard.
- [ ] **Step 3: Verify** with `ffprobe`: duration between 315 and 585 s, 1920×1080, h264 + aac. Extract one frame per chapter and view each for overflow and legibility; listen-check is not possible, so also confirm the narration WAV lengths match the scene durations.
- [ ] **Step 4: Run** every `00-python-foundation-review/examples/*.py` directly and confirm exit code 0.
- [ ] **Step 5: Commit** `feat(video-builder): module 00 video scenes`. Push, open a draft PR, subscribe to its activity, and send the MP4, `metadata.md`, `chapters.txt` and `thumbnail.png` to the user.
