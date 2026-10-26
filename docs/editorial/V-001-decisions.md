# V-001 M2c human decision register

**Status: awaiting actual human review and authorisation. This packet records no approval.**

The M2b preparation PR is merged; the dataset is still draft. M2c completes editorial acceptance
only when a real reviewer supplies the decisions below, authorised changes are applied, and
publication-readiness validation passes. The engineering CLI workstream may proceed separately.

## Material under review

Baseline: `669ac84195aab0dfb25fe7713b540055fee13c10` (merged M1/M2a/M2b/M3a).
These SHA-256 values identify the existing draft input bytes supplied for this review, not future
approved files. Approval metadata changes will legitimately change the snapshot hash; record
resulting hashes after applying authorised changes and before final publication validation.
If facts, assets or the pool change during review, identify the exact changed material and obtain
explicit acceptance of that final version instead of carrying an earlier sign-off forward silently.

| Material | SHA-256 |
| --- | --- |
| Country snapshot | `401ac107f1ca5266f40c2fd6fd91e4c23a226e7012d9bc6f58f9e715f4badfba` |
| V-001 recipe | `15fc1b18110ed8f3df94ddf078b0dda0213d4024989a4871a9db6a79bfdbe97a` |
| Asset provenance register | `e7312d48aeef60c50d8278c31fe67ce053089612d4921b85280b823df560bbac` |
| Flag contact sheet | `1494066a121f5314512c5d5d55fd78352f78df2a5acb9f4c5e3ec3cdd80da173` |

- [Country-by-country evidence and exact reveal sentences](V-001-evidence.md).
- [Step-by-step UAT and artwork/fact/rights checkboxes](V-001-review.md).
- [Source-specific copyright and use-context concerns](asset-licences.md).
- [Exact artwork provenance and per-file checksums](asset-provenance.json).
- [Labelled contact sheet](flag-contact-sheet.png); inspect full-size `assets/flags/*.png` too.

## Actual reviewer details

Supply actual details when the review occurs. Research access dates and Codex preparation do not
supply reviewer identity or review dates. Blank fields below are intentional.

- Reviewer identifier:
- Actual review date (`YYYY-MM-DD`):
- Explicit human authorisation link/message/reference:
- Reviewed baseline/changed commit and input/asset versions:

If multiple people review different facts/assets, record the reviewer/date and authority for each
applicable decision rather than attributing all review to one person.

## Per-country dispositions

Use `accepted`, `rejected`, `correction required`, or `pending`. An accepted country must have its
identity, exact flag and exact learning explanation reviewed, including reliable sources,
seven-second reading, easy-quiz suitability and rights/use-context evidence. Record required
attribution/permission or a supported human conclusion that none is required for the intended
monetised educational video. Public-domain copyright metadata alone does not answer that question.
Country sources/assets do not change through this template; no pending row authorises an update.

| Country ID | Disposition | Corrections / exact accepted wording or artwork version | Rights / attribution / permission evidence | Reviewer / actual date / authorisation reference |
| --- | --- | --- | --- | --- |
| `france` | pending | | | |
| `japan` | pending | | | |
| `canada` | pending | | | |
| `brazil` | pending | | | |
| `germany` | pending | | | |
| `italy` | pending | | | |
| `spain` | pending | | | |
| `ireland` | pending | | | |
| `sweden` | pending | | | |
| `norway` | pending | | | |
| `finland` | pending | | | |
| `denmark` | pending | | | |
| `poland` | pending | | | |
| `greece` | pending | | | |
| `india` | pending | | | |
| `south-korea` | pending | | | |
| `mexico` | pending | | | |
| `argentina` | pending | | | |
| `south-africa` | pending | | | |

Portugal is not a proposed candidate. Its existing flag-colour concern remains unresolved and it
must stay excluded. Add it only through a separately described corrected asset and explicit human
approval; its retained research record/PNG does not constitute acceptance.

## Rights and special-case decisions

- **Canada**: pending. Resolve the particular artwork's business-use/permission question for the
  actual planned monetised educational video. Cite the reviewed source notice, any permission
  required/obtained, and the reviewer's explicit decision. If unresolved, it stays unverified;
  a human may direct its removal from the final candidate pool.
- **Sweden**: pending. Review the commercial-mark/official-endorsement restriction for the actual
  depiction and record the disposition and supporting evidence.
- **Other national-symbol restrictions**: pending. Record applicable display, orientation,
  attribution and use conditions per country, with sources or permission evidence where relevant.
- **Portugal**: excluded. Colour correction/replacement and re-entry are not authorised here.
- **South Africa**: pending. Confirm the identity/flag/reveal material; retain three role-labelled
  capitals and the judicial-capital caveat. Flag review does not approve capital or outline facts.
- **Regional/display conventions**: pending. Confirm Mexico's North America / Central America
  grouping, South Korea's display name, and France's metropolitan classification noted in evidence.

## Final candidate pool and recipe acceptance

The present proposed pool is:

`france`, `japan`, `canada`, `brazil`, `germany`, `italy`, `spain`, `ireland`, `sweden`, `norway`, `finland`, `denmark`, `poland`, `greece`, `india`, `south-korea`, `mexico`, `argentina`, `south-africa`.

It is a proposal, not an approved set. Supply the exact final accepted IDs below; there must be at
least 15, every included country must have an accepted disposition, and none may retain blocking
fact/asset/rights questions. Do not silently infer the final set from passing structural validation.

- Final approved candidate IDs: pending.
- Explicit acceptance of this exact final candidate pool and snapshot: pending.
- Timing: **355 seconds (5:55)** = intro 14 + 15×21-second questions + two 4-second checkpoints
  after questions 5 and 10 + outro 18. Human acceptance: pending.
- Working title: **Guess 15 Countries From Their Flags**. Human acceptance: pending.
- Thumbnail hook: **How many flags can you name?** Human acceptance: pending.
- Fixed seed: **20261026**; changing it requires an explicit recipe decision and later manifest UAT.
- Theme reference: **`geography-pilot`**. Acceptance of this identifier as a future configuration
  reference: pending. **This is not visual-theme UAT.** No theme configuration exists; visual
  presentation design, graphics and rendering remain for a separate reviewed milestone.

## Applying authorised decisions

Codex may apply only genuine decisions provided by the human reviewer. Preserve source references
and use actual reviewer identifiers/dates for accepted `identity`, `flag` and `flag_learning_fact`
verification records. Do not automatically approve unreviewed capital or outline categories.
Apply only specifically authorised factual/artwork/pool corrections, update asset hashes and
provenance when artwork changes, and keep unresolved countries unverified. Set snapshot approval
metadata only after the exact final snapshot/pool is explicitly accepted. Record resulting file
hashes, authorisation references and any deviations below, then rerun the real validators.

- Changes actually authorised and applied: none.
- Resulting snapshot SHA-256: pending.
- Resulting recipe SHA-256: pending.
- Approved asset/provenance revisions/checksums: pending.

## Final gates and later manifest review

From the editorial checkout, run:

```bash
uv run quiztalcoatl validate \
  --countries data/countries.json --recipe recipes/V-001.json \
  --content-root . --publication-ready
uv run pytest tests/test_v001_content.py -v
make check
make smoke
```

The publication command must exit 0 before M2c can be called complete. Its current expected exit 1
for missing editorial approval is recorded accurately, never replaced with fabricated metadata.
The automated content tests follow the genuine production review state. Passing CI is an
engineering result, not a substitute for these human decisions. Keep the editorial PR draft until
its acceptance gates pass; no automatic merge.

After M2c and M3b are complete and merged, generate the actual manifest, repeat into a second
temporary output and compare bytes/input hashes. A human must then inspect all 15 actual resolved
questions: correct flags/answers, three distinct valid distractors, answer indices, explanations,
sources/assets and overall difficulty. Record those real results separately; this pending input
review does not approve a future manifest or the future visual presentation.

- Publication validation result on genuinely approved inputs: pending.
- Editorial CI status/link: recorded in the M2c PR; never a human sign-off.
- Human manifest UAT: pending; actual manifest not yet approved.
