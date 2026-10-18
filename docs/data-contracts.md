# Version 1 data contracts

Google Sheets is the editorial planning and curation system. Reviewed, versioned JSON
snapshots committed to Git are the authoritative local build inputs. Loading, validation
and eventual rendering must not query the Sheet or any source URL. M2a provides contracts
and validation only; it does not import, resolve or publish content.

## Validation and review boundary

All models forbid unknown fields and use strict Pydantic v2 validation. Versioned roots
require integer `schema_version: 1`. Strings must contain non-whitespace text; IDs are
lowercase kebab-case (`test-country-01`), video IDs use `V-001` form, and SHA-256 values
are 64 lowercase hexadecimal characters. Booleans and numbers are not accepted as
strings. Dates in JSON use ISO `YYYY-MM-DD`. No input file is changed or repaired.

Structural validation checks schema, unique IDs/names, candidate references, and supplied
local assets that exist. A draft may omit verification, explanations and asset references;
an asset reference may point to a file not acquired yet. An existing referenced asset
must be a regular file and match its checksum even in draft mode. Unsafe references,
including symlinks escaping the content root, always fail when checking local inputs.

Publication readiness is a separate, explicit gate. The snapshot must be approved with
reviewer/date metadata, and **every candidate in the recipe pool**, not just the eventual
15 selected countries, must have:

- Explicit flag-identification eligibility.
- Verified identity, flag asset and flag learning fact review records.
- A sourced learning explanation and an existing, checksum-matching PNG flag.
- Recognised licence metadata and any required attribution.

Unselected countries outside the candidate pool need not pass publication review. Their
structures and any existing asset references are still checked. A missing outline does
not invalidate flag inputs. Capital/outline eligibility is retained as editorial data;
M2a does not implement recipes or publication gates for those future question formats.

Neither schema validity nor an `approved` string proves factual or legal correctness.
Review status is explicitly supplied by humans; the software never writes approval or
verification metadata. Sources are recorded, never fetched, and source presence alone
is not evidence of accuracy. Publication validation checks recorded metadata and local
files; it does not authenticate reviewers, establish legal rights or verify source claims.

## Editorial contracts

| Contract | Fields and rules |
| --- | --- |
| `SourceReference` | Required HTTP(S) `url`; optional `title`, ISO `accessed_on`. |
| `AssetReference` | Required `path`, `sha256`, HTTP(S) `source_url`, `licence`; optional `attribution`, `notes`. Paths use relative POSIX syntax with no `..`, Windows drive or absolute prefix. |
| `CapitalCity` | Required `name`; optional `role`, `notes`. Store each capital as a separate object, never a slash-delimited list. |
| `VerificationRecord` | Required `status` (`needs_verification` or `verified`) and `sources` list. `verified` requires at least one source, `verified_by` and ISO `verified_on`. |
| `Eligibility` | Three required booleans: `flag_identification`, `capital_questions`, `outline_identification`. No inferred eligibility. |
| `CountryVerification` | Required `identity` review; optional `capitals`, `flag`, `outline`, `flag_learning_fact` reviews. |
| `LearningFact` | Required `text` (1–500 characters, not whitespace only) and non-empty `sources`. Country fact review lives in `verification.flag_learning_fact`. |
| `CountryRecord` | Required `country_id`, `name`, `continent`, `region`, `capitals`, `eligibility`, `verification`; optional `flag`, `outline`, `flag_learning_fact`, `notes`. |
| `CountrySnapshot` | Required `schema_version`, kebab-case `snapshot_id`, `editorial_status` (`draft` or `approved`), non-empty `countries`. Approved snapshots require `approved_by` and ISO `approved_on`. |

Country IDs and display names must be unique; display-name comparison ignores case and
repeated/leading/trailing whitespace. Original display text is preserved. Capital lists
may be empty in drafts or contain multiple role-labelled cities, so South Africa-style
cases do not lose data. Simple capital-question eligibility requires exactly one capital;
one capital alone never turns that eligibility on. A multiple-capital country can still
be explicitly eligible for flags.

Asset paths are relative to the selected content root, normally the repository root for
production snapshots. Supply `--content-root` explicitly when snapshots live in a nested
data directory. By default the CLI uses the country JSON file's parent directory, making
fixture validation independent of the current working directory. Internal symlinks are
permitted only when their resolved destination remains inside the root. File bytes are
hashed with SHA-256. Publication flags require both a `.png` extension and PNG data that
Pillow can verify; M2a does not download, convert or judge the artwork.

The initial publication licence metadata policy recognises `public-domain`, `CC0-1.0`,
`CC-BY-4.0`, and `CC-BY-SA-4.0`; the two attribution licences also require `attribution`.
Other non-empty identifiers can be recorded in drafts but fail publication validation
as unknown/unsupported. This deliberately explicit initial list is a contract decision,
not a claim that other licences are unsuitable. M2b must review actual asset provenance,
rights and attribution requirements and propose any needed policy extension for review.
Empty/whitespace licence strings fail structurally; use `unknown` for an unresolved draft.

## Recipe and timing

`QuizRecipe` requires `schema_version`, `video_id`, `topic`, `quiz_format`, `difficulty`,
`scope`, `question_count`, `candidate_country_ids`, integer `seed`, `distractor_count`,
`timing`, kebab-case `theme_id`, and `publication`.

Only `Geography` / `flag_identification` / `Easy` / `World` are currently permitted, with
three distractors. Counts must be positive; the explicit candidate pool must contain
unique IDs, at least as many countries as questions, and at least four countries to
supply distinct answer options. Joint input validation rejects IDs absent from the
snapshot. V-001 requires exactly 15 questions. No candidate is selected in this milestone.

`Publication` requires `working_title` and `thumbnail_hook`. These are planning text,
not generated YouTube metadata. `Timing` requires:

- Integer `question_seconds: 21` for the approved cycle.
- Finite, non-negative numeric `intro_seconds`, `checkpoint_seconds`, `outro_seconds`.
- `checkpoint_after`: ascending, unique, positive question ordinals strictly before the
  final question (an empty list means no checkpoints).

Checkpoint positions are explicit so the resolver/renderer need not invent placement.
The total is `intro + question_count × 21 + checkpoint_count × checkpoint_seconds + outro`.
Actual intro/checkpoint/outro values remain editorial inputs; fixture numbers below are
illustrative, not approved production timing. No per-frame timeline is introduced.

## Resolved output contracts

`ResolvedQuestion` requires `ordinal`, kebab-case `question_id`, `prompt`, `correct_answer`,
ordered `options`, zero-based `correct_answer_index`, `asset`, `explanation`, and non-empty
`sources`. Answers/options contain `country_id` and display `label`. There must be exactly
four options with unique IDs and unambiguous labels, and the full correct answer must
match the option at the specified index. An explanation uses `LearningFact`; the asset
contains its path, checksum and provenance. Question objects inherit their manifest's
schema version and video ID rather than duplicating them.

`ResolvedQuizManifest` requires `schema_version`, `video_id`, ordered `questions`,
`recipe_sha256`, `snapshot_sha256`, `seed`, `theme_id`, `timing`, and
`expected_total_seconds`. Input checksums identify the original UTF-8 file bytes, not a
re-serialized approximation. Question IDs must be unique and ordinals consecutive from
1; V-001 contains exactly 15 questions. Expected duration must equal the timing formula
(within 0.000001 seconds). No renderer needs to select answers or look up editorial facts.
A theme ID refers to future local theme configuration; it is not a live data reference.

These output types validate internal consistency only. M2a does not produce manifests,
verify that their input hashes correspond to supplied files, or infer editorial approval
from a manifest. M3 will populate them from inputs that pass the publication gate and
record the actual input checksums, seed and ordered choices. JSON round-trip tests cover
snapshots, recipes and manifests, including their nested contracts.

## Test-only examples and commands

The complete small synthetic examples are
[`countries.draft.json`](../tests/fixtures/countries.draft.json) and
[`V-001.test.json`](../tests/fixtures/V-001.test.json). They contain **no real country facts,
verified editorial sources or production assets**. They intentionally fail publication
readiness. Approved test cases generate tiny PNGs in pytest temporary directories and
use `TEST-ONLY-REVIEWER` and `example.invalid`; these are never production approval.

A draft review record:

```json
{"status": "needs_verification", "sources": []}
```

A synthetic multi-capital representation:

```json
{
  "capitals": [
    {"name": "Test Administrative City", "role": "administrative"},
    {"name": "Test Legislative City", "role": "legislative"}
  ],
  "eligibility": {
    "flag_identification": true,
    "capital_questions": false,
    "outline_identification": false
  }
}
```

Illustrative timing (not approved production timing):

```json
{
  "question_seconds": 21,
  "intro_seconds": 5,
  "checkpoint_seconds": 3,
  "checkpoint_after": [5, 10],
  "outro_seconds": 5
}
```

Run the structural fixture validation:

```bash
uv run quiztalcoatl validate \
  --countries tests/fixtures/countries.draft.json \
  --recipe tests/fixtures/V-001.test.json
```

Add `--publication-ready` to see the explicit missing-editorial-approval failure. For
future reviewed inputs with repository-relative asset paths:

```bash
uv run quiztalcoatl validate \
  --countries path/to/countries.json --recipe path/to/V-001.json \
  --content-root /absolute/path/to/quiztalcoatl --publication-ready
```

Success exits 0; invalid input exits 1. Diagnostics distinguish unreadable/invalid UTF-8
files, malformed JSON, schema violations, unknown references and missing publication
approval/verification. Schema failures include field locations; asset/publication failures
include country IDs. Duplicate JSON object keys and non-standard NaN/Infinity tokens are
rejected. Validation stops at the first content-level error; Pydantic reports applicable
schema errors together. `load_snapshot` and `load_recipe` perform structural loading;
`validate_inputs` performs joint reference/asset checks and the optional publication gate.

## Next milestones

M2b will curate and verify actual V-001 facts, review capital ambiguities and eligibility,
acquire approved PNG assets with provenance/checksums/licensing, and commit reviewed
snapshots and recipes. M2a's fixtures are not a substitute for that work.

M3 will implement deterministic selection and distractor resolution, preserve answer
ordering, compute input checksums and produce validated manifests from publication-ready
inputs. No selection, manifest generation, graphics, rendering, Sheet integration,
network access, publishing or additional infrastructure is implemented here.
