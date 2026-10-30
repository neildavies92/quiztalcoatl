# V-001 deterministic video renderer (M5)

M5 extends the existing publication-gated resolver and M4a graphics into one complete
1920×1080, 30 fps, H.264/yuv420p MP4. It preserves the mascot, midnight-jungle palette,
ordered two-by-two options and sourced explanations. It does not select questions or
introduce a second graphics/theme framework.

The real V-001 snapshot remains draft. A successful synthetic technical render is not
editorial, visual, pacing or audio approval, and is not a publication-ready real pilot.

## Production command and validation

```bash
uv run quiztalcoatl render \
  --countries data/countries.json --recipe recipes/V-001.json \
  --manifest output/V-001/manifest.json --content-root . \
  --output output/V-001/video.mp4
```

The current real draft fails closed before producing output. There is no approval bypass.
The renderer calls the existing `resolve_files`, which performs local structural/asset
checks and complete publication-readiness validation. It loads the supplied manifest
through the existing strict JSON loader and requires exact model equality with fresh
deterministic resolution: source hashes, question order/IDs, prompt, answers/options,
correct index, explanation, sources, assets, seed, theme and timing must all match.
Stale, edited or wrong-input manifests must be regenerated, not silently repaired.

Fonts use M4a's explicit `--font-dir` / `QUIZTALCOATL_FONT_DIR` contract. The default brand
path is `assets/brand/quiztalcoatl-logo.png` under the content root; `--brand-asset` can
select an explicit local transparent PNG. Docker supplies the DejaVu font directory.
Native developers must configure their own directory; no workstation search or download
is introduced. The CLI also supports `--overwrite`, solely for replacing a verified final
output. It never relaxes content approval or manifest equality.

## Integer-frame timeline

Only the initial V-001 flag-identification pacing is supported. All timeline frame fields
must be actual integers; floats and booleans do not qualify. At 30 fps:

| Segment | Seconds | Frames |
| --- | --- | --- |
| Intro | 14 | 420 |
| Question/thinking | 14 | 420 per question |
| Correct answer and explanation | 7 | 210 per question |
| Checkpoint after questions 5 and 10 | 4 each | 120 each |
| Outro | 18 | 540 |
| Total | **355** | **10,650** |

The 14/7 split inside the existing 21-second cycle is a **production proposal pending
human pacing UAT**; no recipe/model timing fields are changed. The first question starts
at frame 420 (14 seconds), its reveal at frame 840 (28 seconds); checkpoints start at
frames 3570 and 6840 (119 and 228 seconds); outro starts at 10110 (337 seconds).

`build_timeline` preserves all 15 ordered question/reveal pairs and references. It rejects
unsupported frame rates/formats, missing/misordered questions, mismatched reveal content,
wrong segment positions, gaps, overlaps, non-positive durations and incorrect totals.
Optional `content_root` checks assets without requiring FFmpeg. No cumulative float-time
addition is used; seconds are converted into fixed integer frame counts.

## Rendering strategy and reproducibility

The renderer generates one reusable Pillow card per timeline segment and only fourteen
small transparent timer tiles, not 10,650 individual 1080p PNGs. Question/reveal cards use
M4a `render_card` unchanged. Intro, checkpoints and outro reuse the same palette, fonts
and actual mascot with minimal consistent text. Private M4a `_text`/`_brand` helpers keep
scene fitting and transparency validation consistent; this narrow internal coupling must
be updated together if those helpers are refactored.

FFmpeg overlays the tiny countdown sequence on each question: `14s` through `01s`, each
visible for one exact second, then the seven-second reveal. The timer is in the clear
header space between progress pips and question numbering. Scene cuts and the changing
counter provide purposeful visual progression; there are no elaborate transitions or
animation plugins. Intro explains the challenge, checkpoints prompt score keeping, and
outro asks for the final score with a concise participation invitation.

Each segment is encoded with explicit subprocess arguments, libx264, `veryfast`, CRF 20,
constant 30 fps, yuv420p and two encoder threads. Filter threads are bounded to one.
Segments have identical stream settings and are joined with FFmpeg concat stream copy,
then fast-start MP4 metadata placement. Metadata is stripped and bitexact flags are used;
no generation timestamps or machine paths are inserted into logical content. The source
manifest's original-input-byte checksum semantics and ranking algorithm are unchanged.

`render_video` also accepts `ultrafast` and `medium` presets for explicit API/benchmark
experiments; the production CLI deliberately uses `veryfast`. The logical timeline and
content are reproducible. Byte-identical media is tested for repeated short encodes in
the same controlled FFmpeg/font/library environment; encoder/library changes across
platforms are not promised to produce identical H.264 bytes or rasterized pixels.

## Audio decision

**The technical baseline is silent video-only, with no audio stream.** This is intentional,
not a claim that silence is the final channel experience. It avoids undocumented music
rights and segment AAC-padding drift. No music, voice, sound effects or copyrighted audio
is acquired or generated. Human audio UAT must decide whether narration, licensed music
or effects are needed before publication. The verification contract explicitly expects
one video stream and no audio in this milestone.

## Atomic output and diagnostics

`--output` is explicit and must end in `.mp4`. Existing files require `--overwrite`;
symlink and directory destinations are rejected. Resolved paths and hard-link aliases
cannot replace input country/recipe/manifest JSON, any supplied snapshot flag/outline,
the channel artwork or either font file. Missing optional unused assets can remain absent
under M2a's existing policy; the selected flags must pass the complete gate.

Output directories are created only after content, exact manifest, timeline, fonts,
brand and executable validation. Graphics, segments and final MP4 live in a temporary
directory on the destination filesystem. `ffprobe -count_frames` actually decodes/counts
the finished video and verifies one H.264/yuv420p 1920×1080 stream, both 30/1 rate fields,
exact expected frame count, duration within one frame, and a non-empty file. Invalid
probe JSON/metadata gives an actionable content error.

Only verified output is published atomically, via no-clobber hard link or explicit
replacement. Exceptions clean temporary files and preserve previous final output.
Source hashes are rechecked to detect ordinary edits during rendering. This is not an
adversarial filesystem transaction or power-loss durability guarantee. FFmpeg failures
and timeouts retain available stderr context in diagnostics; successful warning stderr
is retained in the returned `RenderReport` and synthetic benchmark JSON. Redirect CLI
stderr to a user-selected log when retaining failure logs is useful.

## Automated verification and CI smoke

```bash
uv run pytest tests/test_timeline.py tests/test_video.py -v
uv run pytest tests/test_video.py -m smoke -v
make check
make smoke
```

The new real-media test is marked `smoke`, so existing native and container `make smoke`
CI steps discover it without workflow changes. It runs the production card-generation,
encoding/concat and probing paths on a four-second representative sequence: two seconds
of a question with countdown 14→13, one second reveal and one second checkpoint.
It checks 120 actually decoded frames, 1080p/H.264/yuv420p/30 fps, duration, no audio,
non-empty output and actual decoded images. The two countdown crops are compared against
their correct timer templates, the correct tile's decoded gold fill is checked, and the
checkpoint must be visually distinct. A repeated encode must be byte-identical in the
controlled environment. A full 355-second render is intentionally not run in every CI job.

Unit tests cover exact timeline/order/content, integer types, invalid inputs, strict
fresh-manifest matching, publication gating, asset and subprocess failures, useful timeout
stderr, output/alias protection, cleanup, prior-output preservation, verification failures,
concurrent source edits and source immutability. Existing tests and media checks remain.
Native parallel agents used separate pytest basetemp directories to avoid shared cleanup.

Required developer/container commands:

```bash
uv sync --locked
make format
make lint
make typecheck
make test
make check
make smoke
make docker-build DOCKER_IMAGE=quiztalcoatl:m5
make docker-check DOCKER_IMAGE=quiztalcoatl:m5 DOCKER_TEST_IMAGE=quiztalcoatl:m5-test
make docker-smoke DOCKER_IMAGE=quiztalcoatl:m5 DOCKER_SMOKE_DIR=output/m5-container-smoke
git diff --check
git status --short
```

## Full synthetic render and measured performance

`docs/render_synthetic.py` reuses the existing explicitly synthetic approved fixture
producer, writes a resolved synthetic manifest and invokes the full production renderer.
Every scene is visibly marked `SYNTHETIC TECHNICAL PREVIEW • NOT FOR PUBLICATION`.
It never changes the real country data or asserts a genuine human editorial review.

Native reproduction with explicitly available fonts:

```bash
uv run python docs/render_synthetic.py \
  --font-dir /tmp/quiztalcoatl-fonts \
  --brand-asset assets/brand/quiztalcoatl-logo.png
```

Actual offline installed-package Docker reproduction from the M5 worktree:

```bash
make docker-build DOCKER_IMAGE=quiztalcoatl:m5
mkdir -p output/m5-synthetic
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD/docs,dst=/preview-docs,readonly" \
  --mount "type=bind,src=$PWD/assets/brand,dst=/brand,readonly" \
  --mount "type=bind,src=$PWD/output/m5-synthetic,dst=/work/output" \
  --entrypoint python quiztalcoatl:m5 /preview-docs/render_synthetic.py \
  --output-root /work/output --brand-asset /brand/quiztalcoatl-logo.png --preset veryfast
```

A genuine full-length run was executed on 2026-10-30 in the actual rebuilt M5 runtime
(no application source overlay), Linux ARM64, Python 3.12.16, Docker Desktop with 12 CPUs
and about 7.65 GiB available memory. Observed:

| Measurement | Actual result |
| --- | --- |
| Verified duration / decoded frames | 355 seconds / 10,650 |
| Format | 1920×1080, constant 30 fps, H.264, yuv420p, video-only |
| Wall time, including graphics/encoding/verification | 199.623 seconds |
| Final MP4 | 6,490,217 bytes |
| Encoding | veryfast, CRF 20, two encoder threads |
| Temporary files at measured peak | 24,781,240 bytes |
| CPU including children | 440.545 CPU seconds; 220.69% average |
| Largest individual FFmpeg child RSS | 285,995,008 bytes |
| Renderer process RSS | 83,234,816 bytes |
| Sampled container memory | 418.3 MiB during encoding |
| Warnings / failures | 15 image2 thread-queue backpressure warnings; no render failure |

The RSS fields describe individual process maxima, not a summed aggregate peak. Temporary
storage is measured before publication when all cards, parts and completed MP4 coexist.
The queue warnings are retained in `benchmark.json`; they indicate encoder/input buffering
backpressure, not missing/incorrect frames. Exact duration/frame validation passed despite
them. No warnings are suppressed to claim a cleaner benchmark.

Outputs are ignored Git artifacts: `output/m5-synthetic/video.synthetic.mp4`,
`manifest.synthetic.json` and `benchmark.json`. Benchmark timing/RSS/warnings are diagnostic
measurements, not deterministic manifest fields. The benchmark names its output relatively
and retains original manifest checksum; no machine path is added to quiz content.

## Human viewing/audio UAT — pending

Developer/parent QA independently extracted actual encoded frames at 2s (intro),
14.2s (question/countdown), 28.2s (reveal), 119.2s (checkpoint) and 340s (outro),
and inspected them at 960×540. The timer, gold correct answer, mascot and synthetic
annotation were clear, with no visible clipping in those samples. This does not mean
the entire video was watched or that pacing/audio were accepted.

A human must watch the complete synthetic video and record actual reviewer/date,
pass/fail and specific corrections. Engineering tests do not grant this approval.

- [ ] Intro makes the 15-question challenge and score keeping clear.
- [ ] All 15 questions appear in manifest order; flags/options remain legible on mobile.
- [ ] Countdown runs 14→1 at one-second steps; reveal occurs at the intended boundary.
- [ ] Correct indices and explanations belong to the displayed flags.
- [ ] The seven-second explanations can be read comfortably.
- [ ] Checkpoints appear after questions 5 and 10 and feel appropriately paced.
- [ ] Scene cuts, mascot and text are coherent; no flicker, freezing or corruption appears.
- [ ] Silent/no-audio baseline is explicitly accepted or further audio is specified with rights.
- [ ] Outro asks for the final score naturally; total playback is 5:55.
- [ ] Revised M4a appearance is actually accepted; merged graphics alone did not record UAT.

Real V-001 editorial/rights approval remains outstanding. After M5 and M6a are reviewed
and merged, rebuild the combined runtime, obtain genuine country-content approval, resolve
and inspect the real manifest, then render and review the full real package. No cloud,
queue, database, publishing/scheduling API, new quiz format or external media framework
is included in M5. Thumbnail/publication output remains a separate M6a workstream.
