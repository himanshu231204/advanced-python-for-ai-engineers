# video-builder

Builds one YouTube video per learning module for the
[BitYodha](https://www.youtube.com/@BitYodha) channel, fully automatically:
scene spec (YAML) -> Pillow frames -> offline Piper narration -> ffmpeg MP4.

Design: [`docs/superpowers/specs/2026-10-22-module-videos-design.md`](../docs/superpowers/specs/2026-10-22-module-videos-design.md)

## Requirements

- Python 3.12+ and `ffmpeg` (with libx264) / `ffprobe` on PATH
- Fonts at the Debian/Ubuntu paths `fonts-inter` and `fonts-dejavu-core` install (`apt install fonts-inter fonts-dejavu-core`); on other systems edit `bityodha/theme.py`
- `pip install -r requirements.txt`
- First build downloads the Piper voice (`en_US-lessac-medium`, about 60 MB) into `voices/`

## Build a module video

```bash
cd video-builder
python3 -m bityodha.build 00-python-foundation-review
```

Outputs go to `out/<module>/`: `video.mp4`, `chapters.txt`, `metadata.md`, `thumbnail.png`.
The build fails if the final video is shorter than 5:15 or longer than 9:45, if an
on-screen example does not run, or if any text does not fit the frame.

## Add a module

Create `modules/<module-folder>/scenes.yaml`. Scene types: `title`, `concept`, `code`,
`output`, `compare` (bullets as `left | right`, first row is the header), `recap`, `outro`.
`code` scenes slice `lines: [start, end]` from a real repo file; `output` scenes run the
file and show its real output.

## Tests

```bash
cd video-builder
python3 -m pytest -q
```
