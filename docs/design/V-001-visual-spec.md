# V-001 visual specification — geography-pilot, revision 2

## Review status and scope

The first paper/field-guide proposal was **rejected by Neil Davies in chat on
2026-10-27**. His actual feedback was:

> It looks absolutely terrible I'm not going to lie, it looks really boring.

His subsequent direction was:

> It needs to be engaging and include the channel logo/mascot in it

Revision 2 responds with a dark, energetic quiz-show composition, a much larger flag,
logo-matched emerald/gold/coral accents, huge question typography and a two-by-two answer
grid. The supplied mascot is a substantial part of the composition. There is no `ART TBC`
rectangle, worksheet panel, instruction paragraph or prototype-approval text in the
viewer composition. A small synthetic-preview footer remains outside the content safe area.

**Approved requirements:** 1920×1080 PNGs, clear mobile-scale flag identification,
four resolved options, 15-question progress, preserved artwork proportions, correct-answer
reveal and a short sourced explanation. Neil explicitly authorized use of the particular
supplied logo/mascot. This does not establish third-party rights or approve the new frame.

**Proposed, pending Neil's visual UAT:** the revised palette, spacing, typography, mascot
scale, hero composition, reveal treatment and future motion ideas. No statement below
means that PNG generation or green CI constitutes human design acceptance.

**Independent editorial gate:** real V-001 country content is still draft. These previews
use fictional countries, a generated geometric flag and explicitly test-only review
metadata. No real content is approved, resolved or modified for this design exercise.
The existing `geography-pilot` identifier remains sufficient; no theme/plugin framework
or production CLI extension is introduced.

## Channel artwork

The exact supplied artwork is prepared as
[`assets/brand/quiztalcoatl-logo.png`](../../assets/brand/quiztalcoatl-logo.png), a
1254×1254 RGBA PNG with true alpha transparency. Its preparation, original/prepared hashes
and exact background-extraction prompt are documented in
[`assets/brand/README.md`](../../assets/brand/README.md). The background extraction was
performed with the built-in imagegen edit tool; pixel-for-pixel identity of opaque
artwork to the original is not claimed. No alternate mascot was invented.

The renderer receives artwork through the explicit `brand_asset` path. It preserves the
entire square logo, including the feathered serpent, glasses, cap, book, circular badge
and wordmark, without clipping or stretching. No image is fetched at runtime. The loader
rejects missing/corrupt files, non-PNG data, opaque RGB/fully opaque PNGs and wholly
invisible artwork. A visible image with genuinely transparent background is required,
preventing a white-background rectangle from silently entering the composition.

The supplied character visibly anchors the right-hand hero area. A compact typographic
QUIZtalcoatl name remains in the header for sequence continuity. Proposed-composition
status lives in documentation/diagnostic metadata, rather than replacing the mascot or
adding distracting labels over viewer content.

## Visual direction and palette

Use a midnight jungle/navy stage, emerald answer badges, vivid gold for the brand and
success, and restrained coral accents. Angular background planes and a floating flag
shadow add depth without a white document panel or decorative clutter. All critical
header text sits on a uniform actual background, so its measured contrast metadata
matches the surface behind it. Answer and explanation text have explicit solid surfaces.

| Role | Colour | Use |
| --- | --- | --- |
| Midnight background | `#071F26` | Header and main canvas |
| Deep ink | `#062329` | Type on gold; selected answer badge |
| Emerald | `#17634F` | Answer letter badges and completed progress pips |
| Deep-teal surface | `#12383E` | Answer tiles and explanation strip |
| Gold | `#FFD45B` | Brand, current pip, correct headline/tile and answer letters |
| Coral | `#FF976A` | Small edge/fact accent |
| Soft white | `#F7FFF7` | Question and answer text |
| Muted light | `#BDD7CD` | Synthetic-preview footer |
| Quiet border | `#2E6763` | Tile edges and header divider |

Measured sRGB contrast ratios: white/midnight 16.71:1, white/teal surface 12.40:1,
gold/emerald 5.05:1, ink/gold 11.58:1 and muted/midnight 11.16:1. Tests require at
least 4.5:1 for every actual text block's declared foreground/background pair. Reveal
meaning is also conveyed through explicit `CORRECT ANSWER` text and the correct country
name; colour is not the only signal.

## Typography and font contract

Production previews use **DejaVu Sans regular and Bold** through an explicit `font_dir`
or `QUIZTALCOATL_FONT_DIR`. Required files are `DejaVuSans.ttf` and
`DejaVuSans-Bold.ttf`. The M3c container supplies Debian `fonts-dejavu-core` at
`/usr/share/fonts/truetype/dejavu`. No font binary is committed here.

The loader reads those exact files into memory before FreeType sees them. Pillow's
filename API can otherwise silently fall back to a system font when an explicit file
is missing or corrupt. There is no implicit workstation lookup, startup download or
new dependency. Missing/corrupt files produce actionable diagnostics naming the directory.

Tests inject Pillow's embedded Aileron FreeType face in memory. Temporary embedded-font
copies exercise explicit loading without pretending to be production DejaVu artwork.
Tests require no workstation fonts or network. Determinism is checked within controlled
font/Pillow/FreeType environments; native and Linux container rasterization need not be
pixel-identical across different native libraries. The container font/library environment
is the proposed canonical production baseline.

| Text | Size at 1920×1080 | Behaviour |
| --- | --- | --- |
| Header wordmark | 35 px Bold | Compact, single line |
| Question / correct country | 78 px maximum, 52 px minimum Bold | Centered; question up to two lines, reveal name one line |
| Answer labels | 48 px maximum, 36 px minimum Bold | Up to two measured lines |
| A/B/C/D | 53 px Bold | Oversized, distinct badges |
| Educational fact | 38 px maximum, 34 px minimum regular | Up to two measured, balanced lines |
| Progress | 34 px Bold | Direct resolved ordinal / explicit total |
| Correct-answer label | 24 px Bold | Gold pill |
| Fact label | 23 px Bold | Compact two-line label |
| Synthetic annotation | 18 px | Outside viewer-content safe area |

Wrapping uses measured font advances, and final fitting checks actual glyph ink bounds,
including negative bearings. Line advance is `ceil(size × 1.22)`. Candidate sizes decrease
in whole pixels only inside the documented range. Two-line explanations are balanced by
measured width so a single final word is not stranded on its own line. The original
fact text is preserved; only display wrapping changes.

Unbreakable names or text that cannot satisfy the stated width, height and readable
minimum produce a `GraphicsError` identifying the role and required bounds. Nothing is
silently clipped, truncated, ellipsized or shrunk without limit. The model's 500-character
fact limit does not mean a 500-character explanation fits this reveal; such text needs
an editorially reviewed shorter version or a reviewed layout revision.

## Composition and safe area

Coordinates are x, y, width, height. Important text/artwork stays inside the 72 px content
safe area `(72,72,1776,936)`. Decorative planes/shadows and the synthetic footer are not
critical viewer information.

| Element | Geometry / treatment |
| --- | --- |
| Header | Small gold name at left, explicit progress at right, 15 compact pips in the middle |
| Progress pips | Completed = emerald; current = gold; remaining = dark teal. The ordinal is not inferred. |
| Question headline | `(72,162,1776,118)`; centered, large and directly from the resolved prompt |
| Question flag bounds | `(144,294,1100,440)`; large floating artwork, no white worksheet panel |
| Question mascot bounds | `(1270,264,560,470)`; complete supplied image, aspect fit |
| Reveal label/title | Gold `CORRECT ANSWER` pill followed by country in `(72,216,1776,100)` |
| Reveal flag bounds | `(144,328,1100,278)`; smaller to reserve readable explanation space |
| Reveal mascot bounds | `(1270,294,560,320)`; maintains a visible character beside the flag |
| Four answers | Two-by-two: x=72 or 982; y=764 or 896; each 866×112 |
| Answer mapping | A/B first row, C/D second row, in existing manifest order |
| Explanation strip | `(72,626,1776,118)` with coral accent and clear fact label |
| Explanation text | `(260,636,1556,96)`; two readable lines maximum |

The flag and brand image each use the smaller of their width/height scale factors and
Lanczos resizing. The original aspect ratio is retained to integer-pixel rounding; wide,
square and portrait flags remain different shapes. PNG alpha is composited over the stage
(white only immediately behind a transparent flag's own bounds), not onto an oversized
white panel. Asset paths/checksums/PNG validity are checked through the existing M2a
validator. Brand artwork has its own explicit local transparent-PNG check.

Question and reveal keep answer positions identical. Reveal highlights exactly the
existing correct index in gold, retains all four options and places the original sourced
fact in a separate strip. No country selection, answer reordering, invented explanation
or resolver change occurs here. Sources remain in the existing manifest; visual rendering
does not establish factual correctness, rights ownership or editorial approval.

## Minimal typed API and output safety

```python
from pathlib import Path
from quiztalcoatl.graphics import CardLayout, load_fonts, render_card, save_png

# question comes from genuinely approved inputs or clearly synthetic test-only fixtures.
card = render_card(
    question,
    CardLayout(total_questions=15),
    content_root=Path("/work"),
    fonts=load_fonts(Path("/usr/share/fonts/truetype/dejavu")),
    reveal=False,
    brand_asset=Path("assets/brand/quiztalcoatl-logo.png"),
)
save_png(card, Path("output/static-cards"), "question-01.png")
```

The existing API is retained; `brand_asset` is an optional explicit path, with no fake
logo fallback. Successful channel previews require the supplied asset. `RenderedCard`
returns the image and measured text/flag/brand geometry, source paths, original option
IDs and highlighted index. Its `design_status` records that the composition is a proposal
awaiting human UAT. These diagnostics are not a new editorial or rendering manifest.

The mutable question model is revalidated before rendering. `CardLayout` supplies total
question count explicitly; ordinals outside it fail. A resolved question has no human
review state of its own, so callers must preserve the existing publication/resolver gate.

`save_png` only accepts contained relative POSIX `.png` output paths. Traversal, absolute
or Windows paths, symlink escapes, existing final symlinks and aliases of either source
flag or brand image fail. Existing outputs require `overwrite=True`. Writes use a flushed,
fsynced temporary file in the same directory, then atomic no-clobber hard linking or
explicit replacement; failures clean temporary output and preserve previous files.
Filesystems without hard-link support fail safely. This is not an adversarial filesystem
transaction or a power-loss durability guarantee. Inputs are not mutated; rendering is offline.

## Reproducible revision-2 previews

```bash
uv run python docs/design/preview.py \
  --font-dir /tmp/quiztalcoatl-fonts \
  --brand-asset assets/brand/quiztalcoatl-logo.png
```

Or set `QUIZTALCOATL_FONT_DIR` and omit `--font-dir`. The helper creates synthetic approved
test inputs below ignored `output/design-v2/inputs`, resolves them through the actual
publication gate, and generates `question.png`, `reveal.png`, `stress.png`, and corresponding
480×270 `*-mobile.png` files in `output/design-v2/`. `--output-root` selects another
explicit directory. Repeated runs explicitly replace these named PNGs. No production
country fact, recipe or approval record is changed. All content/examples are clearly
synthetic; the only real supplied artwork is the authorized channel mascot/logo.

The stress case uses long fictional country names and a longer fictional fact. Review
it at both full HD and mobile size. Preview outputs remain ignored rather than committed.
The source brand PNG and its preparation record are committed as the explicit runtime
resource supplied by Neil; no font binary is distributed.

If using the built M3c runtime, its DejaVu files can be copied to `/tmp` for native QA:

```bash
container_id=$(docker create quiztalcoatl:local)
mkdir -p /tmp/quiztalcoatl-fonts
docker cp "$container_id:/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" /tmp/quiztalcoatl-fonts/
docker cp "$container_id:/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" /tmp/quiztalcoatl-fonts/
docker rm "$container_id"
```

For a provisional offline cross-branch check from the graphics worktree:

```bash
mkdir -p output/design-v2-container
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD/src,dst=/preview-src,readonly" \
  --mount "type=bind,src=$PWD/docs/design,dst=/preview-tools,readonly" \
  --mount "type=bind,src=$PWD/assets/brand,dst=/preview-brand,readonly" \
  --mount "type=bind,src=$PWD/output/design-v2-container,dst=/work/output" \
  -e PYTHONPATH=/preview-src --entrypoint python quiztalcoatl:local \
  /preview-tools/preview.py --font-dir /usr/share/fonts/truetype/dejavu \
  --brand-asset /preview-brand/quiztalcoatl-logo.png --output-root /work/output
```

Parent QA executed the revision-2 command with read-only source/tool/brand mounts,
disabled networking, read-only container root/tmpfs and mapped host UID/GID. All six
mascot-backed PNGs had the expected formats/dimensions and host-user ownership; two
runs produced byte-identical output for all six files. The source logo checksum stayed
unchanged. The parent inspected the actual container mobile reveal without identifying
clipping or a white logo rectangle.

This is actual runtime source-overlay compatibility evidence, not a rebuilt installed
revision-2 package or human design approval. Native vs container pixel identity is not
promised. After both branches merge, rebuild the runtime with graphics included and
rerun without the source/PYTHONPATH overlay. M4a changes no Dockerfile, Makefile, CI
workflow, content contract or production CLI.

## Verification and human acceptance

Run all baseline quality commands, plus:

```bash
uv run pytest tests/test_graphics.py -v
uv run mypy src tests docs/design/preview.py
uv run python docs/design/preview.py \
  --font-dir /tmp/quiztalcoatl-fonts \
  --brand-asset assets/brand/quiztalcoatl-logo.png
```

Tests retain the existing guarantees for controlled-font determinism, actual text draw
operations/geometry, resolved content and order, ordinal, reveal pixels, safe margins,
contrast, aspect ratios, long text, font/asset failures, offline use, no input mutation
and safe output. New tests cover the two-by-two geometry, current pip, actual alpha artwork
composition, brand proportions/source protection and opaque/invisible/corrupt rejection.
No fragile cross-platform golden screenshot replaces these checks.

**Actual review record:** Neil rejected revision 1 with the quoted feedback above.
Developer/parent implementation QA found the revision-2 direction substantially improved:
large clear flag, naturally composited supplied logo, readable answer grid and obvious
gold reveal. This is QA feedback, not Neil's acceptance. Full-HD question/reveal and
mobile question/long-text stress previews were inspected. The revised fact strip keeps
a 34 px minimum; impossible text still fails explicitly.

**Revision 2 human design UAT — pending.** At full HD and mobile scale, record actual
reviewer/date, pass/fail and specific requested changes:

- [ ] Is this engaging enough for the channel, rather than boring or worksheet-like?
- [ ] Does the supplied mascot feel naturally integrated and appropriately prominent?
- [ ] Is the flag the main question evidence and large enough to recognize?
- [ ] Is the question instantly understandable, with all four answers easy to scan?
- [ ] Does the two-by-two layout preserve a clear A/B/C/D reading order?
- [ ] Is the correct-answer reveal unambiguous without relying only on colour?
- [ ] Can the exact learning fact be comfortably read in about seven seconds?
- [ ] Are the long-name and long-fact cases readable at mobile scale?
- [ ] Do the colours, typography and depth support repeated viewing across 15 questions?
- [ ] Is important content within safe margins, without clipping or a logo background box?

Record actual feedback; do not equate automated tests with design approval. Editorial UAT
of the real V-001 candidate pool/rights/facts and later real-manifest UAT remain independent.

## Future presentation proposals — not implemented

Potential motion is a restrained question entrance, a clear countdown tied to existing
progress context, and a short gold success emphasis while retaining answer positions.
These need visual review before implementation. No MP4, FFmpeg timeline, countdown
animation, transitions, audio, thumbnail, publishing feature or competing theme system
is introduced by this static redesign.
