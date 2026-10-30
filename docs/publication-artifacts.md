# Thumbnail and publication review package

M6a generates `thumbnail.png`, `title.txt`, `description.txt` and `metadata.json`
under an explicit output directory, conventionally `output/V-001/`. It does not
upload, schedule, approve editorial material or claim that a video has passed UAT.
Google Sheets remains the planning tracker; Git holds approved source snapshots.
This package is generated output, not a second catalogue.

`publication.generate_package` is the production library entry point. It invokes
`resolve_files` with the existing publication gate, loads the supplied manifest
through the strict JSON loader, and compares the complete manifest with fresh
resolver output. Changed source bytes, stale manifests, modified prompts, missing
or corrupt artwork, missing verification and unsupported licences fail before
publication output is created. The current real V-001 snapshot remains draft and
is expected to fail. No skip-validation option exists.

The thumbnail uses the first three questions in their resolved order without
reselecting countries. Each thumbnail flag therefore belongs to the approved,
locally checksum-validated manifest. It reuses `graphics` font loading, text fitting,
asset validation, aspect fitting and the supplied transparent mascot. The poster
composition differs from the question card: large left headline, three flag samples,
a prominent right mascot and a gold challenge strip. Jungle/emerald/gold/coral colours
remain consistent with the current design proposal. Impossible hooks fail explicitly;
text is never clipped or silently truncated. The minimum 64 px hook becomes 16 px at
a 320×180 search-size preview. Geometry/contrast checks supplement human viewing.

## Export requirements checked against YouTube

The [official YouTube Help page](https://support.google.com/youtube/answer/72431?hl=en)
was read on 2026-10-30. It currently recommends **3840×2160** for video thumbnails,
with a minimum width of 640 px, JPG/PNG and 16:9. Its stated device limits are
2 MB for video thumbnails uploaded on mobile and 50 MB on desktop. Account
verification and thumbnail policies also apply.

This milestone deliberately retains the brief's initial **1280×720 RGB PNG** target:
it is 16:9 and exceeds the minimum width, though below the current recommended
resolution. Export rejects files at or above a conservative 2,000,000 bytes for
portable uploads. Recheck the official page before actual publication. No network
lookup happens during package generation.

## Metadata and rights review

The exact recipe title and hook are preserved. Copy invites viewers to choose four
answers, keep score and share a score or surprising flag. Suggested tags are a short,
fixed list. Titles over 100 characters or containing control characters fail; a
description over 5,000 UTF-8 bytes also fails, with no discarded attribution.
Angle brackets are rejected in title/description. These limits follow the current
[official video resource reference](https://developers.google.com/youtube/data/reference/rest/v3/videos#snippet.title).

Every selected flag's source URL, licence, exact attribution and notes are retained
in `metadata.json`. Source URLs, licence names and exact attribution text also appear
in the description; potentially long internal provenance notes stay in metadata. The ordered factual source records are
retained in metadata and linked in the description. Original snapshot/recipe/manifest,
brand and thumbnail SHA-256 values identify the inputs and output. No timestamps,
absolute machine paths, network responses or random generation affect serialization.
Repeated runs with the same source bytes, fonts, Pillow and container environment
produce identical artifacts. Cross-platform font raster byte identity is not promised.

`review_status` is always `pending_human_review`: a verified editorial snapshot is a
prerequisite, not approval of thumbnail composition, copy, derivative artwork licensing
or the final video. Review source-specific restrictions and any share-alike obligations
for the final combined artwork. The existing Canada/Sweden questions and Portugal
exclusion remain in the editorial packet; M6a changes none of them.

## Output safety and video coexistence

The four owned artifacts coexist with `manifest.json`, `video.mp4` and other output
files. Existing owned artifacts require `overwrite=True`; unrelated files are untouched.
Sources, including hardlink aliases, and symlink destinations are protected. All bytes
are staged and fsynced before committing. A sibling exclusive lock serializes calls
through this API. Each final file is installed atomically; ordinary commit failures
restore prior owned files (or remove newly installed files) and clean temporary files.

There is no cross-file filesystem transaction: readers can briefly observe mixed
versions during the four renames, and abrupt power loss or rollback disk failure can
leave incomplete output. Wait for a successful return before consuming the package;
rerun after inspecting any interrupted output. A stale `.V-001.publication.lock` may
be removed only after confirming no generation process is active. External writers
must not modify source or destination files during generation. Input byte and resolver
checks are repeated immediately before publication.

## Synthetic preview: exact reproduction

Successful previews use explicitly synthetic approved fixture records, fictional flags,
`TEST-ONLY-REVIEWER` and `example.invalid` sources. These are never applied to real
country data. The helper reuses M4a's fixture builder, creates distinct geometric flags,
and marks its working title `SYNTHETIC PREVIEW`. The small PNG is a review aid outside
the four-file package.

Native (DejaVu files must be supplied explicitly as in the existing graphics docs):

```bash
uv sync --locked
uv run python docs/publication_preview.py \
  --font-dir /tmp/quiztalcoatl-fonts \
  --output-root output/publication-synthetic
```

Actual runtime with no source overlay, using the installed application and runtime fonts:

```bash
make docker-build DOCKER_IMAGE=quiztalcoatl:m6a
mkdir -p output/publication-container
docker run --rm --network none --read-only --tmpfs /tmp \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD/docs,dst=/preview-tools,readonly" \
  --mount "type=bind,src=$PWD/assets/brand,dst=/preview-brand,readonly" \
  --mount "type=bind,src=$PWD/output/publication-container,dst=/work/output" \
  --entrypoint python quiztalcoatl:m6a \
  /preview-tools/publication_preview.py \
  --brand-asset /preview-brand/quiztalcoatl-logo.png \
  --output-root /work/output
```

Open `output/publication-container/V-001/thumbnail.png` (1280×720),
`output/publication-container/thumbnail-mobile.png` (320×180), title, description
and metadata. The synthetic manifest and source files are retained alongside for
reproduction. Run the command twice and compare all four output hashes.

After genuine editorial approval, the library call is:

```python
from pathlib import Path
from quiztalcoatl.graphics import load_fonts
from quiztalcoatl.publication import generate_package

metadata = generate_package(
    Path("data/countries.json"),
    Path("recipes/V-001.json"),
    Path("output/V-001/manifest.json"),
    content_root=Path("."),
    brand_asset=Path("assets/brand/quiztalcoatl-logo.png"),
    fonts=load_fonts(),
    output_directory=Path("output/V-001"),
)
```

Use the runtime's documented read-only source/brand mounts and writable output mount;
the recipe and manifest must already correspond to the genuinely approved inputs.
Set `overwrite=True` only when deliberately replacing the four publication artifacts.
No shared production CLI is changed in this independent workstream.

## Verification and manual UAT

Required baseline commands plus dedicated tests:

```bash
uv sync --locked
make format
make lint
make typecheck
make test
make check
make smoke
uv run pytest tests/test_thumbnail.py tests/test_publication.py -v
uv run mypy --strict src tests docs/publication_preview.py
make docker-build DOCKER_IMAGE=quiztalcoatl:m6a
make docker-check DOCKER_TEST_IMAGE=quiztalcoatl:m6a-test
make docker-smoke DOCKER_IMAGE=quiztalcoatl:m6a DOCKER_SMOKE_DIR=output/m6a-container-smoke
git diff --check
git status --short
```

Automated coverage includes actual PNG output, supplied brand composition, measured
readable hook floor, margins/contrast, aspect ratios, controlled deterministic bytes,
missing/corrupt artwork, long copy, source/approval rejection, no network, attribution,
immutable sources, coexistence with video/manifest, overwrite aliases, lock handling,
source mutation and injected commit failure rollback. Existing FFmpeg smoke remains.

Human UAT is **pending**. Automated image inspection is preparation QA only.
Reviewer: ______  Date: ______  Result: ______  Feedback: ______

- [ ] Inspect full-size and 320×180 thumbnails; read the main hook without zooming.
- [ ] Confirm visual appeal, supplied mascot and jungle/gold channel consistency.
- [ ] Confirm safe margins, no clipping and recognisable, correctly proportioned flags.
- [ ] For production, match each flag to its approved artwork and review licence/attribution.
- [ ] Confirm title/hook/description reflect the actual video with no misleading claims.
- [ ] Confirm the call to action feels natural and tags remain relevant.
- [ ] Inspect exact credits, modifications/rights notes and source links.
- [ ] Confirm the complete video and thumbnail package suits an educational channel.

M4a design acceptance, M5 pacing/audio/playback UAT and real-country editorial sign-off
remain separate pending gates. There is no upload, scheduling, AI service, new dependency,
shared model/CLI change or video-renderer dependency in M6a.

## Recorded implementation QA (2026-10-30)

Native and Linux Docker checks passed: 272 unit tests, 33 dedicated M6a tests,
Ruff/strict mypy, existing real FFmpeg smoke and the runtime acceptance driver.
The helper was additionally checked with strict mypy alongside application/tests.
A concurrent native pytest run initially lost its shared temporary directory;
rerunning with a workstream-specific `PYTEST_ADDOPTS=--basetemp=/tmp/quiztalcoatl-m6a-pytest`
passed. No test or application behavior was bypassed.

Two actual `quiztalcoatl:m6a` runtime preview executions used installed application
code (no source/PYTHONPATH overlay), networking disabled, a read-only root/docs/brand,
tmpfs and mapped host UID/GID. All 29 generated source/manifest/review files were
byte-identical between runs and host-owned. The thumbnail was 354,033 bytes;
its SHA-256 was `3ac7f6b084c49c15c9617d485a23280af0df9463d66a8d60fef599cd4bc5db4b`.
The first complete preview took 1.24 seconds wall-clock on the local ARM64 Docker
Desktop environment (including container startup and synthetic fixture generation).
Native preview generation measured 0.43 seconds; this is an observation, not a
performance guarantee.

Agent preparation QA inspected the full 1280×720 and 320×180 actual runtime PNGs:
the main hook was readable, the supplied mascot prominent and the three fictional
flag samples distinct. The secondary gold strip is intentionally smaller. The
synthetic title, participation copy, exact source records and pending review status
were inspected. Parent QA of the preliminary design found the headline readable,
mascot prominent and composition distinct. Neither inspection constitutes human
visual acceptance. Host preview files are ignored outputs under
`output/publication-container/`; no PNG/MP4 or fake editorial approval is committed.
