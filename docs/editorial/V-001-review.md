# V-001 human editorial UAT and approval

**Preparation only. No human has signed off. Keep the M2b PR in draft.**

## Reproduce preparation checks

From the M2b checkout, run:

```bash
uv sync --locked
uv run pytest tests/test_v001_content.py -v
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
   **355 seconds (5:55)**. Confirm working title, thumbnail hook and theme identifier; the theme
   itself does not yet exist. Record final timing UAT acceptance.

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
required rights/permission evidence in this PR or review document. There is no pre-filled reviewer
identity or review date. Do not bulk mark records verified merely because these tests are green.

For the final candidate pool, update applicable `identity`, `flag` and `flag_learning_fact`
verification records to `verified` only after the actual review, preserving source links and
setting `verified_by` and `verified_on` from that explicit approval. Review capitals separately if
changing their review status or enabling later eligibility. Remove any rejected/unresolved candidate
from the recipe, preserving at least 15. Portugal remains excluded unless its artwork issue is
resolved and that candidate is explicitly approved. Set snapshot `editorial_status: approved`,
`approved_by` and `approved_on` only after final snapshot approval with real details.

Rerun the full checks and the actual `--publication-ready` command above. It must exit 0 before M2b
is complete and before making the draft PR ready for review/merge. The content tests conditionally
require the genuine approved input to pass rather than fabricating approval in test code.

Then request human code/content review. Do not auto-merge. M3b integration may begin only after
M2b and M3a are reviewed and merged; no real manifest, resolver CLI or video output is produced here.

## Approval record

- Human reviewer: pending.
- Actual review date: pending.
- Per-country checkboxes/dispositions: pending.
- Canada/Sweden and other use-context decisions: pending.
- Portugal exclusion/remediation: excluded; remediation pending if desired.
- Recipe timing/title/theme UAT: pending.
- Snapshot approval: absent.
- Final publication-ready validation: expected failure until genuine approval.
