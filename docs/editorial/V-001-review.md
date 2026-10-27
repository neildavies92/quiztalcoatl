# V-001 human editorial UAT and approval

**M2c acceptance is pending. No human has signed off. Keep the M2c editorial PR in draft.**

M2b preparation ([PR #4](https://github.com/neildavies92/quiztalcoatl/pull/4)) and M3a
resolution ([PR #3](https://github.com/neildavies92/quiztalcoatl/pull/3)) are merged in reviewed
`main` commit `669ac84195aab0dfb25fe7713b540055fee13c10`. Merging preparation and passing CI did
not approve the production snapshot: it remains `draft`, its 19 proposed candidates remain
unverified, and Portugal remains excluded. M3b CLI engineering proceeds independently and must
reject these inputs until the genuine publication gate passes.

Use [the M2c decision register](V-001-decisions.md) to supply actual reviewer/date details,
per-country decisions, rights evidence and explicit final-pool/recipe acceptance. Its fields are
pending capture, not a sign-off or authorisation to change production metadata.

## Reproduce preparation checks

From the M2c checkout based on the reviewed `main` commit above, run:

```bash
uv sync --locked
uv run pytest tests/test_v001_content.py -v
make check
make smoke
uv run quiztalcoatl validate --countries data/countries.json --recipe recipes/V-001.json --content-root .
uv run quiztalcoatl validate --countries data/countries.json --recipe recipes/V-001.json --content-root . --publication-ready
```

The first validation currently succeeds structurally; the last command currently exits 1 because
editorial approval is missing. That is the intended gate, not a defect to bypass.

## Inspect the exact content

1. Read [the evidence register](V-001-evidence.md) beside `data/countries.json` and
   `recipes/V-001.json`. Confirm all 19 candidate IDs are easy and appropriate for the audience.
2. Open [the labelled contact sheet](flag-contact-sheet.png), then each full-size
   `assets/flags/<country-id>.png`. Inspect at 100% for correct association, design, ratio,
   orientation, clipping, corruption and watermarks. Compare with the linked exact source and
   official national-symbol guidance, including emblem details and digital colour approximations.
3. Follow every explanation's evidence link and assess the exact short wording, not merely source
   existence. Read each sentence aloud within seven seconds. Resolve any historical/symbolic
   discrepancy; shorten or remove a claim rather than invent certainty.
4. Check display spelling and UN subregion/continent conventions, especially Mexico, South Korea,
   France's overseas scope and South Africa's separately role-labelled capitals. Simple capital
   questions are disabled throughout the pilot.
5. Review [licence evidence and open rights questions](asset-licences.md). Resolve Canada's
   business-use/permission question, Sweden's mark/endorsement restriction and applicable
   national-symbol use conventions. Record evidence of any permission required for the actual use.
6. Review the 21-second cycle with intro 14, checkpoints 4 after questions 5 and 10, outro 18:
   **355 seconds (5:55)**. Record explicit acceptance of working title
   `Guess 15 Countries From Their Flags`, thumbnail hook `How many flags can you name?`,
   and the `geography-pilot` identifier as a reference for future theme configuration.
   **Identifier acceptance is not visual-theme UAT**: no visual theme configuration exists;
   visual presentation must be reviewed separately in the future design milestone.
7. Complete the [decision register](V-001-decisions.md) with the actual reviewer identifier/date,
   one disposition for each proposed country, precise corrections, rights/permission evidence,
   and the exact final candidate IDs (at least 15). Decisions such as “accept all remaining
   countries” must identify that set unambiguously. A green test result or merged PR cannot fill
   these fields. Unresolved countries stay unverified; exclusion from the recipe requires the
   reviewer's actual disposition, with Portugal continuing its existing exclusion unless a
   corrected asset is separately reviewed and approved.

## Country checklist

Each checkbox covers these mandatory checks:

- **Artwork**: country association, design, normative ratio, orientation, no clipping/corruption/watermarks.
- **Geography**: spelling, regional convention and any capital/geographical ambiguity.
- **Fact/source**: exact explanation accuracy, authoritative source and seven-second delivery.
- **Rights**: particular asset copyright/provenance, use restrictions and attribution/permission.
- **Easy/quality**: appropriate difficulty and overall candidate suitability.

All boxes start unchecked; automated tests and Codex visual inspection do not fill them.

| Country ID | Artwork | Geography | Fact/source | Rights | Easy/quality | Disposition / reviewer notes |
| --- | --- | --- | --- | --- | --- | --- |
| `france` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `japan` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `canada` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `brazil` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `germany` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `italy` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `spain` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `portugal` | [ ] | [ ] | [ ] | [ ] | [ ] | Excluded pending colour review |
| `ireland` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `sweden` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `norway` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `finland` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `denmark` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `poland` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `greece` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `india` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `south-korea` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `mexico` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `argentina` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |
| `south-africa` | [ ] | [ ] | [ ] | [ ] | [ ] | Pending human review |

## Record real approval only after UAT

The reviewer supplies their real identifier, actual review date, per-country disposition and any
required rights/permission evidence in this PR or the linked M2c decision register. There is no
pre-filled reviewer identity or review date. Do not bulk mark records verified merely because these tests are green.

For the final candidate pool, update applicable `identity`, `flag` and `flag_learning_fact`
verification records to `verified` only after the actual review, preserving source links and
setting `verified_by` and `verified_on` from that explicit approval. Review capitals separately if
changing their review status or enabling later eligibility. Remove any rejected/unresolved candidate
from the recipe, preserving at least 15. Portugal remains excluded unless its artwork issue is
resolved and that candidate is explicitly approved. Set snapshot `editorial_status: approved`,
`approved_by` and `approved_on` only after final snapshot approval with real details.

Rerun the full checks and the actual `--publication-ready` command above. It must exit 0 before M2c
is complete and before making the M2c draft PR ready for review/merge. The content tests conditionally
require the genuine approved input to pass rather than fabricating approval in test code.

Then request human code/content review. Do not auto-merge. M3b engineering may be reviewed and
merged independently while these inputs remain unapproved. Generate the real V-001 manifest only
after both M3b and M2c are complete and merged, publication validation succeeds, and the exact
approved input/asset set is available. Repeat resolution into a second temporary output file,
compare bytes and input hashes, then conduct human UAT on all 15 actual resolved questions.
No real production manifest or visual-theme approval is claimed by this document.

## Approval record

- Human reviewer: pending.
- Actual review date: pending.
- Per-country checkboxes/dispositions: pending.
- Canada/Sweden and other use-context decisions: pending.
- Portugal exclusion/remediation: excluded; remediation pending if desired.
- Final candidate pool (at least 15 explicit IDs): pending.
- Recipe 355-second timing acceptance: pending.
- Working title and thumbnail hook acceptance: pending.
- `geography-pilot` identifier acceptance: pending.
- Visual-theme UAT: future milestone; no theme configuration exists or is approved.
- Snapshot approval: absent.
- Final publication-ready validation: expected failure until genuine approval.
