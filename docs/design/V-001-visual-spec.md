# V-001 visual specification — geography-pilot (M4a proposal)

## Status and approval boundary

**Approved project requirements:** 1920×1080 landscape PNGs, a general-audience flag quiz,
four ordered answer options, 15-question progress context, preserved flag proportions,
clear reveal and a short educational explanation. Existing editorial and resolver
contracts remain authoritative. The eventual cycle is 21 seconds; no timeline is built here.

**Proposed design decisions:** all palette, typography, spacing, wordmark treatment,
static card composition and future motion ideas below. These are reviewable M4a choices,
not an approved visual theme. `geography-pilot` remains the existing identifier; there
is no theme/plugin configuration system.

**Pending human design UAT:** engagement, character, mobile readability, repeated viewing,
mascot artwork, transition/countdown presentation and final visual acceptance. Automated
geometry tests and the developer's visual checks do not supply that approval.

**Independent editorial blocker:** the real V-001 snapshot remains draft. Content merge
and green CI are not human approval. No production fact, flag or verification record is
changed by this work. The previews use fictional countries and generated geometric flags
with conspicuous test-only review metadata. They are not a real resolved V-001 quiz.

## Design direction

A friendly field-guide aesthetic: warm paper, deep teal ink, a gold learning accent,
strong type and generous space. The flag is the main visual evidence; the prompt and
four answer tiles provide a clear left-to-right reading path. A restrained edge rule,
soft shadows and rounded panels repeat consistently without elaborate decoration.

The scholarly feathered-serpent mascot is a future brand asset. No approved transparent
mascot exists in the repository. The header reserves a 64×64 slot labelled `ART / TBC`;
the adjacent text explicitly says `PROPOSED WORDMARK • MASCOT PENDING`. The proposed
QUIZtalcoatl wordmark is typography only. No unapproved logo, AI replacement or white
background logo rectangle is shipped. Actual mascot artwork needs preparation, rights
review, transparent-background inspection and separate design acceptance.

## Palette and contrast

| Role | Colour | Use |
| --- | --- | --- |
| Warm paper | `#F4F1E8` | Background |
| Deep ink | `#183B3D` | Main type, progress pill, reveal fact panel |
| Forest teal | `#145C56` | Section labels and correct-answer tile |
| Gold | `#F1C86C` | Correct letter badge and learning label |
| White | `#FFFFFF` | Flag/answer surfaces and reveal text |
| Muted ink | `#506665` | Prototype status and secondary metadata |
| Quiet rule | `#D9E1D8` | Panel borders and dividers |

Measured sRGB relative-luminance contrast ratios are 10.74:1 for ink/paper, 6.90:1 for
teal/paper, 7.79:1 for white/teal, 7.63:1 for gold/ink and 5.42:1 for muted/paper.
Tests require at least 4.5:1 for every actual text block's foreground/background pair.
Decorative panel borders are not used as the only source of information. Reveal state
has an explicit `THE ANSWER IS` heading and correct country name in addition to colour.

## Typography and font contract

Production previews use **DejaVu Sans regular and Bold**. Supply either an explicit
`font_dir` or `QUIZTALCOATL_FONT_DIR` containing exactly the expected filenames:

- `DejaVuSans.ttf`
- `DejaVuSans-Bold.ttf`

The M3c runtime provides them at `/usr/share/fonts/truetype/dejavu` through Debian's
`fonts-dejavu-core`; the agreed environment variable points there. There is no implicit
workstation font search or fallback, no startup download and no new Python dependency.
The loader reads those exact files into memory before invoking FreeType: Pillow's
filename-based API can otherwise fall back to a system font on some platforms even
when an explicit file is missing or corrupt. Font-loading failures identify the required
files and the supplied directory.

No font binary is committed in this PR. Actual local previews used fonts exported from
the M3c container image to `/tmp/quiztalcoatl-fonts`. Consult the installed Debian font
package copyright file for the DejaVu/Bitstream licence; adding distributed font files
or new typefaces would require explicit licence and design review.

Tests inject Pillow's embedded Aileron FreeType face in memory. Temporary Aileron copies
also test the explicit two-file loader interface; their DejaVu-shaped filenames are
strictly test fixtures and are not represented as production DejaVu artwork. No test
requires a developer's workstation fonts or network access. Pixel identity is promised
only within a controlled font/Pillow/FreeType environment; native and container PNG
compression/rasterization need not be byte-identical across different native libraries.

| Text | Size at 1920×1080 | Behaviour |
| --- | --- | --- |
| Proposed wordmark | 43 px Bold | One line |
| Main prompt / revealed country | 62 px maximum, 48 px minimum Bold | Up to two measured lines |
| Answer labels | 43 px maximum, 36 px minimum Bold | Up to two measured lines |
| Educational fact / instruction | 38 px maximum, 34 px minimum regular | Up to two measured lines |
| Progress / series | 25 px Bold | One line |
| Eyebrows | 23 px Bold | One line |
| Fact label | 22 px Bold | One line |
| Prototype annotation | 19 px | Outside viewer-content safe area |
| Brand status / reserved-art annotation | 16 / 13 px | Secondary prototype-only labels |

Text is greedily wrapped at whitespace using measured font advances. Each candidate
font size is checked against actual glyph ink bounds, accounting for negative bearings.
Line advance is `ceil(font_size × 1.22)`. Sizes decrease by whole pixels only within the
stated range. Long unbreakable words or text exceeding the minimum readable size/two-line
limit raise a `GraphicsError` naming the role, box and minimum size. Nothing is silently
clipped, truncated or ellipsized. The 500-character model limit is not a promise that a
500-character explanation fits this static reveal: overly long facts explicitly fail
and need an editorially reviewed shorter version or a reviewed layout revision.

## Fixed composition and safe area

Coordinate origin is the top-left; dimensions below use x, y, width, height.
Important content remains within the 72 px viewer-content safe margin: `(72,72,1776,936)`.
The edge rule, soft shadows and clearly labelled test-only bottom annotation are decorative
or prototype metadata rather than viewer-critical content.

| Element | Geometry / treatment |
| --- | --- |
| Header | Brand at left; `GEOGRAPHY / FLAGS` in middle; question ordinal/total pill at right |
| Mascot reservation | `(72,72,64,64)`; outline-only placeholder, no logo artwork |
| Progress | `(1500,72,348,68)`; ordinal comes directly from the resolved question |
| Eyebrow and headline | Left column begins x=72, y=190; headline `(72,236,1056,146)` |
| Flag panel | `(72,386,1056,414)`; white surface, subtle rule and shadow |
| Maximum flag bounds | `(128,421,944,344)`; centered, preserve aspect ratio, no crop/stretch |
| Four answer tiles | x=1200, width=648, height=126; y=`244 + index×146` |
| Answer letters | A–D in source option order, not alphabetized by country |
| Footer panel | `(72,846,1776,162)` |
| Fact text | `(104,903,1712,86)`; up to two lines |

The flag is resized with Lanczos using the smaller of width/height scale factors.
The decoded PNG's original width/height ratio is preserved to integer-pixel rounding.
Square, wide and portrait flags have different displayed widths; their artwork is never
forced into a common aspect ratio. PNG alpha is composited on the white panel. Input
assets must pass the existing M2a path-containment, checksum and PNG checks before use.

Question state shows the original resolved prompt, all four labels and a gentle
`Pick A, B, C or D` instruction. Reveal state retains tile positions and flag scale,
changes the headline to the resolved correct name, highlights exactly the supplied
correct-answer index and displays the exact sourced explanation. The graphics layer
never selects countries, invents explanations, reorders options or changes answers.
Sources remain in the existing manifest; this prototype does not invent on-screen
attribution or imply that source/licence approval follows from successful rendering.

## Minimal API

```python
from pathlib import Path
from quiztalcoatl.graphics import CardLayout, load_fonts, render_card, save_png

# question is an existing ResolvedQuestion from genuinely approved or test-only inputs.
fonts = load_fonts(Path("/usr/share/fonts/truetype/dejavu"))
card = render_card(
    question,
    CardLayout(total_questions=15),
    content_root=Path("/work"),
    fonts=fonts,
    reveal=False,
)
save_png(card, Path("output/static-cards"), "question-01.png")
```

`render_card` revalidates its mutable question model and returns a `RenderedCard` with
the RGB Pillow image, actual text/ink geometry, fitted flag bounds, original source
size, option IDs and reveal index. These diagnostics support meaningful tests; they
are not a new editorial or rendering manifest. Sequence context is explicit through
`CardLayout`; ordinal greater than the total fails. The caller supplies approved inputs
or clearly labelled synthetic test content. A resolved question has no editorial-review
state of its own, so graphics cannot authenticate human approval; production integration
must retain the existing resolver/publication gate.

`save_png` accepts only relative POSIX `.png` paths under an explicit output root.
Traversal, absolute/Windows paths, symlink escapes, existing final symlinks and aliases
to the source flag fail. Existing files require explicit `overwrite=True`. A temporary
file is flushed and fsynced in the destination directory, then published atomically
with no-clobber hard linking or explicit replacement; temporary output is cleaned on
failure. There is no unsafe fallback for filesystems lacking hard-link support. This
is local-file safety, not an adversarial filesystem transaction or power-loss guarantee.
PNG generation never mutates input models/assets or uses the network.

## Reproducible previews

From the M4a branch, with M3c's runtime fonts available:

```bash
uv run python docs/design/preview.py --font-dir /tmp/quiztalcoatl-fonts
```

Or set `QUIZTALCOATL_FONT_DIR` and omit `--font-dir`. The helper creates **synthetic-only**
approved test inputs in `output/design-preview/inputs`, resolves them through the real
publication gate, and generates:

- `output/design-preview/question.png`
- `output/design-preview/reveal.png`
- `output/design-preview/stress.png`
- Matching `*-mobile.png` copies at 480×270 for inspection.

All outputs are ignored by Git and are intentionally absent from the committed source.
`--output-root` selects another explicit preview directory. Repeated preview generation
explicitly replaces these named previews; it does not change production data. The stress
example uses long fictional country names and a longer fictional explanation; it does
not claim these labels/facts form an approved real quiz. The main example deliberately
uses an invented geometric flag rather than unapproved national artwork.

To copy font files from a built M3c image without redistributing them in Git:

```bash
container_id=$(docker create quiztalcoatl:local)
mkdir -p /tmp/quiztalcoatl-fonts
docker cp "$container_id:/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" /tmp/quiztalcoatl-fonts/
docker cp "$container_id:/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" /tmp/quiztalcoatl-fonts/
docker rm "$container_id"
```

The M3c Docker font/library environment is the proposed canonical production baseline.
Parent integration QA executed the following provisional cross-branch check from the
M4a worktree, using the actually built runtime and its DejaVu package:

```bash
mkdir -p output/container-design-integration
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD/src,dst=/preview-src,readonly" \
  --mount "type=bind,src=$PWD/docs/design,dst=/preview-tools,readonly" \
  --mount "type=bind,src=$PWD/output/container-design-integration,dst=/work/output" \
  -e PYTHONPATH=/preview-src --entrypoint python quiztalcoatl:local \
  /preview-tools/preview.py --font-dir /usr/share/fonts/truetype/dejavu \
  --output-root /work/output
```

Executed result: all six PNGs had the expected formats/dimensions and host-user ownership;
repeating the same container command produced identical PNG bytes for all six outputs.
The parent visually inspected the container mobile reveal without identifying a layout
issue. Native and container pixels differed, as expected for different native font/
rasterization libraries; cross-platform pixel identity is not claimed. Future production
UAT should inspect these container-generated previews as well as the full-HD originals.

Both branches must be reviewed and merged before final integrated acceptance. The
read-only source overlay above is provisional compatibility QA, not a merge. After both
merge, rebuild the image containing graphics, omit the source/PYTHONPATH overlay and
mount only the preview tool and output directory for final acceptance. No Dockerfile,
Makefile, CI workflow or production CLI change is part of M4a.

## Verification and human visual UAT

Run the baseline `uv sync --locked`, `make format`, `make lint`, `make typecheck`,
`make test`, `make check`, `make smoke`, `git diff --check`, `git status --short`, plus:

```bash
uv run pytest tests/test_graphics.py -v
uv run mypy src tests docs/design/preview.py
uv run python docs/design/preview.py --font-dir /tmp/quiztalcoatl-fonts
```

Automated tests use controlled fonts and check actual draw operations against the text
ledger, exact option order/ordinal, reveal pixels, 1920×1080 PNG encoding, repeated
rendering, measured safe bounds, contrast, several aspect ratios, long-text wrapping and
explicit overflow, font/file failures, source preservation, offline operation and output
traversal/symlink/alias protection. No fragile cross-platform golden PNG is introduced.

Developer visual checks inspected question/reveal full-HD images and question/stress
480×270 images. Observed: clear hierarchy and correct C reveal, distinct readable labels,
preserved flag proportions, no visible clipping or background-box mascot artwork. This
is implementation QA, not a human judgement of channel appeal or approval of the theme.

**Human review record — pending:** reviewer identifier/date and actual feedback have not
been supplied. At full HD and mobile scale, record pass/fail and specific corrections:

- [ ] Question is immediately understandable; flag is large and recognisable.
- [ ] All four answers are readable and easy to scan; long names remain readable.
- [ ] The eye moves naturally from flag to answers without clutter.
- [ ] Correct-answer reveal is obvious without relying on colour alone.
- [ ] The learning fact can be read comfortably during the proposed seven-second reveal.
- [ ] Contrast, warm palette and typography feel professional and fit repeated viewing.
- [ ] Branding is distinctive but unobtrusive; placeholder is not mistaken for approved art.
- [ ] Long-text stress cases are acceptable or produce actionable editorial/layout revisions.
- [ ] Important content remains inside safe margins at TV and mobile viewing sizes.
- [ ] Design is engaging enough for the pilot; record actual feedback, not only test results.

Record accepted/rejected decisions and rerun affected tests/previews after changes. Human
visual approval remains pending until an actual reviewer supplies it.

## Proposed future motion — not implemented

Reserve a simple horizontal countdown treatment near the existing progress context,
with high-contrast remaining time and a final-three-second emphasis. Proposed transitions
are a short crossfade into the static question and a brief highlight/emphasis into the
static reveal, preserving answer positions. These proposals need design review before
a timer, transitions, audio, FFmpeg timeline or full renderer is built. No thumbnail,
publishing, AI graphics, new quiz format or theme framework is implemented here.
