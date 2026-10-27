# QUIZtalcoatl

A local-first application for producing polished educational geography quiz videos for
YouTube. The first planned pilot is **V-001 — Guess 15 Countries From Their Flags**.

M1 establishes the Python package, CLI, environment checks and automated development
checks. M2a adds strict versioned data contracts and offline validation of local JSON,
asset references and publication-readiness metadata. Image cards, full video rendering
and publishing remain future milestones.
M2b supplies researched draft content and assets. M3a/M3b resolve questions deterministically
and expose a production CLI; real V-001 publication still requires M2c human approval.

## Development setup

Requires Python 3.12 or newer, [uv](https://docs.astral.sh/uv/getting-started/installation/),
Make, and FFmpeg including ffprobe and the libx264 encoder. The repository pins the
development interpreter to Python 3.12; uv can download it when necessary.

Install external prerequisites separately:

- macOS with Homebrew: `brew install ffmpeg`; install Xcode command-line tools for Make.
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install ffmpeg make`.
- Windows: use WSL with the Ubuntu instructions above.

Both `ffmpeg` and `ffprobe` must be on PATH. Setup never installs system packages or
requires privileged access itself.

```bash
git clone https://github.com/neildavies92/quiztalcoatl.git
cd quiztalcoatl
make setup
uv run quiztalcoatl doctor
```

`make setup` runs `uv sync --locked` to install the package and development dependencies
from committed `uv.lock`. Initial dependency/interpreter downloads need network access;
the CLI's environment diagnosis and media smoke test work locally without network access.

## CLI

```bash
uv run quiztalcoatl --help
uv run quiztalcoatl --version
uv run quiztalcoatl doctor
uv run python -m quiztalcoatl --help
```

`doctor` reports Python and media-tool versions, and exits non-zero with installation
guidance if either executable is missing or fails to run.

Validate the synthetic test-only draft (this does not grant editorial approval):

```bash
uv run quiztalcoatl validate \
  --countries tests/fixtures/countries.draft.json \
  --recipe tests/fixtures/V-001.test.json
```

Add `--publication-ready` to require approved, verified, licensed inputs and real PNG
flags; the draft fixture intentionally fails that gate. Use `--content-root /path/to/repo`
for repository-relative asset paths; otherwise paths resolve from the snapshot directory.
Validation never modifies files or accesses the network. See
[data contracts](docs/data-contracts.md) for schemas, timing, provenance and review rules.

Resolve approved inputs into readable, reproducible JSON:

```bash
uv run quiztalcoatl resolve \
  --countries data/countries.json --recipe recipes/V-001.json \
  --content-root . --output output/V-001/manifest.json
```

The real snapshot is still draft; this currently fails with an editorial-approval error
and creates no manifest. After genuine approval, the command validates every input,
then writes through a temporary file and publishes atomically. Existing outputs require
`--overwrite`; this never bypasses editorial checks. Keep generated files under ignored
`output/` or `outputs/`. See [resolver usage and synthetic acceptance](docs/resolver.md)
and the [editorial review checklist](docs/editorial/V-001-review.md).

## Development commands

| Command | Purpose |
| --- | --- |
| `make setup` | Synchronise locked dependencies and show prerequisite guidance |
| `make format` | Apply Ruff formatting |
| `make lint` | Check Ruff rules without modifying files |
| `make typecheck` | Run strict mypy on source and tests |
| `make test` | Run isolated unit tests; no FFmpeg installation required |
| `make check` | Validate formatting, lint, types and unit tests without editing source |
| `make smoke` | Render and inspect a real two-second H.264 MP4 with FFmpeg/ffprobe |

`uv run pytest` runs both unit and smoke tests. The smoke test uses a synthetic
320×180, 30 fps source and verifies codec, pixel format, dimensions, duration and file
size with ffprobe. Missing media tools fail explicitly. Generated files go into pytest's
temporary directory and are removed automatically after the test, including on failure.
Keep other generated video/image
outputs under `output/` or `outputs/`, which are ignored by Git.

GitHub Actions runs locked installation, `make check` and `make smoke` on Ubuntu with
Python 3.12 for pull requests targeting `main` and pushes to `main`.

## Docker execution

Native uv development remains supported. Docker supplies Python 3.12, FFmpeg/ffprobe,
Pillow dependencies and an explicit DejaVu Sans font baseline in a non-root CLI image.
Requires Docker, Make and host Python 3.9+ for the standard-library acceptance driver.

```bash
make docker-build
make docker-check
make docker-smoke
docker run --rm --network none quiztalcoatl:local doctor
```

The check target executes static analysis/tests inside an offline test container. The smoke
target exercises the real runtime image, read-only inputs, host-user output permissions,
synthetic approved resolution and H.264 encoding; it leaves a short MP4 under ignored
`output/container-smoke/` for human playback review. Editorial data stays mounted at run
time, so content edits require no image rebuild. The real draft snapshot still fails approval.
See [container usage, pins, volume mounts, fonts and UAT](docs/container.md).
