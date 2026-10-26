# Deterministic flag resolver (M3a)

M3a transforms the existing M2a country and recipe contracts into a validated
`ResolvedQuizManifest`. It supports only flag identification. It performs no network
access, rendering, editorial approval, question reuse tracking or output-file writing.
M3b adds the CLI and output handling below; real V-001 editorial approval remains a separate gate.

## Public interfaces and validation boundary

```python
from pathlib import Path
from quiztalcoatl.resolver import resolve_files

manifest = resolve_files(
    Path("data/countries.json"),
    Path("recipes/V-001.json"),
    content_root=Path("."),
)
```

`resolve_files(countries_path, recipe_path, *, content_root=None)` is the production
input boundary. It uses M2a's `load_snapshot`, `load_recipe` and
`validate_inputs(..., publication_ready=True)`. Draft, unverified, ineligible,
unlicensed, missing-asset or checksum-invalid inputs fail with `ContentError`. Every
country in the explicit recipe pool must pass; the resolver never silently drops bad
candidates. The default asset root is the country JSON file's parent, matching M2a.

Hashes are SHA-256 of the exact original input bytes, including formatting and trailing
newlines. Inputs are reread after loading and publication validation; changes during
that interval fail explicitly instead of recording a hash for different input bytes.
No JSON is written and input files remain untouched. This detects ordinary concurrent
edits; it is not an operating-system transaction or a guarantee against a malicious
file being replaced and restored between reads. Assets should remain stable during
resolution and must be rechecked by the future renderer when consumed.

```python
from quiztalcoatl.resolver import resolve_quiz

manifest = resolve_quiz(
    validated_snapshot,
    validated_recipe,
    snapshot_sha256=original_snapshot_hash,
    recipe_sha256=original_recipe_hash,
)
```

`resolve_quiz` is a pure function accepting valid M2a models and input hash strings.
It checks explicit approval, country eligibility, identity/flag/explanation review
status, required fact/asset references and licence metadata. It deliberately cannot
verify files or prove that the supplied hashes match them. Callers using this lower
level interface are responsible for the M2a structural/file-validation preconditions;
production callers should use `resolve_files`. Neither interface grants factual or
legal approval. `model_construct`, unvalidated `model_copy` updates and mutation can
bypass Pydantic invariants; such objects do not satisfy the pure API's validated-model
precondition. The returned manifest is constructed with the existing Pydantic models,
which validate its ordered questions, answers, input hash syntax and duration.

The pure metadata checks reuse M2a's `_require_verified` and `_require_licence` helpers
to avoid copying editorial/licensing policy. These are private local helpers, so a
future refactor of `content.py` must update this internal coupling together. M3a makes
no changes to the shared contracts, loaders, CLI, dependencies, Makefile or workflow.

## Ranking algorithm: resolver v1

`rank_country_ids` implements the same ranking primitive for question selection,
distractors and displayed option order. For each country ID, form this exact JSON array:

```text
["quiztalcoatl-resolver-v1","flag_identification",domain,seed,question_country_id,country_id]
```

Encode with Python `json.dumps(..., ensure_ascii=True, separators=(",", ":"))`, then
ASCII-encode the resulting text and compute its SHA-256 digest. Sort ascending by the
raw 32-byte digest, using country ID as a deterministic collision tie-breaker.
The integer seed is a JSON integer, including its minus sign for negative values.
No Python `hash()`, random generator, process hash seed, machine path or timestamp
participates in the ranking.

Domains are literal strings:

| Stage | `domain` | `question_country_id` | Result |
| --- | --- | --- | --- |
| Question selection | `questions` | empty string | Rank the explicit pool; take the first `question_count` IDs in this order |
| Distractor selection | `distractors` | correct country ID | Exclude the correct ID; rank the remaining approved pool and take three |
| Option arrangement | `options` | correct country ID | Rank the correct country and selected three distractors; retain that display order |

Candidate and snapshot array order do not affect selection, distractors or option
arrangement. Reordering/reformatting source files does change their original-byte
hashes, so logical questions remain equivalent while manifest input hashes differ.
Source lists and other editorial text are preserved as supplied; changing them is an
input change. The selected country ID is unique per question. Answer IDs and labels
remain those of the approved pool. No geographical similarity or balancing heuristic
is added. The fixed 20-country synthetic fixture naturally uses all four answer
positions, and tests detect regressions to its exact option order.

Changing the namespace, array encoding, domains, seed handling or tie-breaker changes
reproducibility and requires an explicit compatibility decision. Schema version 1 is
unchanged; `resolver-v1` is an algorithm namespace in the ranking bytes, not a new
manifest field.

## Resolved content

Question IDs are `video_id.lower() + "-flag-" + country_id`, for example
`v-001-flag-test-country-16`. They remain stable if the same country moves to another
ordinal. Ordinals are consecutive from 1 in the ranked selection order.
The displayed prompt is `Which country does this flag represent?`.

Each question copies the correct country's flag reference, sourced educational fact
and its source references. The answer index is zero-based and points to exactly the
matching ID/label option. Nested assets, facts, sources and timing are copied so
mutating a returned manifest does not mutate the input models.

The manifest retains the recipe seed, theme and timing. Expected duration is computed
using the existing timing formula, including explicit checkpoint positions. With
14 seconds intro, 15 × 21-second cycles, two 4-second checkpoints and an 18-second
outro, the expected duration is 355 seconds. No rendering timeline is generated.
Stable JSON serialization is `manifest.model_dump_json()`; it contains no generation
time or machine-specific absolute paths. Byte-for-byte identity across future changes
to the contracts or pinned libraries is not promised without compatibility review.

## Fixed vectors

With seed `42`, `question_country_id="alpha"` and IDs `alpha,beta,gamma,delta`, the
ranking primitive must produce:

| Domain | Expected order |
| --- | --- |
| `questions` | `gamma, alpha, delta, beta` |
| `distractors` | `gamma, beta, delta, alpha` |
| `options` | `beta, delta, gamma, alpha` |

For the synthetic 20-country fixture with seed `20261026`, the selected country
suffixes are `16,20,04,07,14,09,12,03,10,18,17,13,15,11,06`. The first question's
options are `15,10,16,05`; its correct-answer index is `2`. Full selection and all
15 answer-position vectors are fixed in `tests/test_resolver.py`.

## Reproducible manual inspection (synthetic, test-only)

Run from this branch:

```bash
uv run pytest tests/test_resolver.py::test_synthetic_manual_inspection -s -q
```

The test creates 20 fictitious countries, a tiny generated red PNG and explicitly
labelled test-only review metadata in a temporary directory. It prints a resolved
question with the seed and hashes calculated from those actual temporary input files.
No real geography facts or genuine editorial approvals are claimed.

The observed example with the committed lockfile is:

| Item | Value |
| --- | --- |
| Seed | `20261026` |
| Stable question ID | `v-001-flag-test-country-16` |
| Prompt | Which country does this flag represent? |
| Correct answer | Test Country 16 |
| Three distractors | Test Country 05, Test Country 10, Test Country 15 |
| Final display order | Test Country 15, Test Country 10, **Test Country 16**, Test Country 05 |
| Zero-based correct index | `2` |
| Snapshot SHA-256 | `f6f948260be75492a89797ce2a1534f5e466561d6633f35e1fed42d6853ad5bf` |
| Recipe SHA-256 | `3cfbfe6ba77907e304ea4db534aa72f110d59e5f631803c64b16e65f336a6eb4` |
| Explanation | TEST ONLY: Synthetic fact 16. |
| Source | `https://example.invalid/synthetic-source` (test placeholder) |

To inspect manually, check that the displayed correct country occurs once at index 2,
that each other option is distinct, and that repeating the command preserves ranking,
option order and seed. The printed hashes identify the exact generated fixture bytes;
fixture-image encoding or input-formatting changes can legitimately change those
hashes. The fixed ranking vectors should remain unchanged.

The synthetic example was executed and inspected during M3a development. Human
inspection of the real V-001 content remains pending M2b approval and M3b integration.

## Verification and follow-on integration

Run `uv run pytest tests/test_resolver.py -v`, `make check` and `make smoke`. Tests
cover fixed vectors, repeated/reordered inputs, alternate seeds, publication failures,
asset errors, exact file hashes, source preservation, JSON round trips, mutation
isolation, offline execution and the expected duration. Existing M1/M2a tests remain
part of the full suite.

M2c editorial acceptance progresses independently using the unchanged contracts. M2b and M3a are now merged. M3b calls `resolve_files` through the production CLI;
real-content output and UAT still require genuine M2c approval and passing publication readiness. M3a itself supplied no real V-001 manifest, CLI resolve command or renderer. The M3b CLI below preserves its algorithm and contracts.

## Production CLI and output safety (M3b)

The production command uses `resolve_files` and the existing publication gate:

```bash
uv run quiztalcoatl resolve \
  --countries data/countries.json --recipe recipes/V-001.json \
  --content-root . --output output/V-001/manifest.json
```

`--output` is required. The real snapshot is currently draft, so this command exits 1
with missing-approval diagnostics and creates no output directory or manifest. Merging
content or passing CI does not approve it. M2c records actual human editorial acceptance;
there is no option to bypass approval, verification, licensing metadata or asset integrity.
`--overwrite` grants permission to replace an output file only after all input gates pass.

After resolution, the manifest is serialized with the existing Pydantic model's field
order, two-space indentation, UTF-8 encoding, LF line endings and exactly one trailing
newline. No timestamps, absolute machine paths or new ranking inputs are introduced.
Repeated resolution of identical files produces identical manifest bytes. Input hashes
continue to identify the original source bytes, and the fixed M3a ranking/answer vectors
remain unchanged. Successful V-001 resolution reports 15 questions and 355 seconds.

Directories are created only after validation and serialization succeed. A temporary
file is created in the destination directory, written, flushed, fsynced and closed before
publication. With `--overwrite`, `os.replace` atomically replaces the destination. Without
it, an atomic hard link publishes the complete temporary file only if the destination
is absent; this also protects an output created concurrently after the initial check.
The temporary link is then removed. Both operations use the destination filesystem.
A filesystem without hard-link support fails explicitly rather than falling back to a
partial or clobbering write. This guarantees atomic publication, not transactional
protection against adversarial filesystem changes or power-loss durability of directory
entries.

Failures in temporary-file creation, writing, syncing or publication leave an existing
output unchanged and remove the temporary file. Empty output directories can remain
after an I/O failure; partially written manifests do not. Existing directories and
symlinks are handled explicitly; an output cannot alias either input JSON file or a
referenced flag/outline asset, including assets not selected for questions. The CLI
reloads the snapshot through the existing loader solely to protect all referenced
asset paths; it does not duplicate validation policy or change the resolver API.

Write generated manifests under the Git-ignored `output/` or `outputs/` directories.
The command never commits files. Example of an intentional repeat run:

```bash
uv run quiztalcoatl resolve \
  --countries data/countries.json --recipe recipes/V-001.json \
  --content-root . --output output/V-001/manifest.json --overwrite
```

### Reproduce synthetic CLI acceptance

```bash
uv run pytest tests/test_resolve_cli.py -v
uv run pytest tests/test_resolve_cli.py::test_installed_cli_demonstration -s -q
```

The second command generates approved **test-only** inputs in a temporary directory,
invokes the real module CLI twice, prints the success summaries and manifest hash,
and compares actual output bytes. No production verification metadata is changed.
The observed synthetic manifest SHA-256 with the committed lockfile was
`68e81de2797b66f67ce48a415a3276e44f4c3d4c9efe4b025f3b354968aa732c`.
This identifies test fixture bytes, not real V-001 content.
The suite also exercises refusal to overwrite without consent, invalid/unapproved
inputs, injected write failures, cleanup, source preservation and the genuine current
editorial state of `data/countries.json`. After real approval that regression requires
successful real-content resolution; it does not hardcode permanent draft status.

Human acceptance of the real 15-question output remains a separate step after M3b and
M2c are reviewed and merged. Check all flags, answers, distractors, explanations,
sources, input hashes and the 355-second duration; generate a second file and compare
bytes. A `geography-pilot` identifier is a reference to future theme configuration,
not proof of visual-theme UAT. This milestone adds CLI integration and output handling;
it does not create a renderer or record editorial acceptance.
