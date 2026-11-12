# Shared demo generation: experiment and release evidence

## Decision

The twelve products form a benchmark corpus. They are not twelve hand-coded product routes. Three subagents audited creative, developer and research tasks, then reviewed the common contract and actual model responses. Earlier product-specific prototypes remain outside the release in ignored local artifacts.

The common runtime now supports four bounded artifacts: editable drafts, searchable/selectable records, configurable local forms and independently mergeable text patches. The model supplies content and complete variants; application code supplies operations, local-execution narration and provenance. Existing examples remain readable unless an exact reviewed spec is withdrawn. Reading never invokes a model.

## Actual provider experiment

The user explicitly authorized **nine total local evaluations**, including the first three. A stable actor and persistent attempt ledger count failures too. The production personal allowance remains 3 and the global site cap remains 20. No actor rotation, counter reset or automatic publication occurred.

| Prompt revision | Product | Provider requests | Structural outcome | Semantic review |
| --- | --- | --- | --- | --- |
| v1 | Melius | 1 | Valid editor | Reject: platform changes product identity; unsupported offers/specifications |
| v1 | Exa | 2 | Invalid | Missing variants and nested bilingual cells/evidence |
| v1 | Lovable | 1 | Valid form | Reject: unenforced 1–10 range and invented email/notification behavior |
| v2 | Melius | 2 | Invalid | Facts flattened into strings; repair still invents quantities |
| v2 | Exa | 2 | Invalid | Unsupported measured claim, then missing literal binding facts |
| v2 | Lovable | 2 | Valid editor | Reject: repair downgraded designing a form to writing a feedback record |
| v3 | Melius | 2 | Valid editor | Reject, 11/15: stable identities, but unsupported features/benefits remain |
| v3 | Exa | 2 | Valid records | Conditional 12/15: accepted after generic narration/search fixes and browser checks |
| v3 | Conductor | 2 | Invalid | Patch targets occur in other replacements, not the original base |

Total: **9 evaluations / 16 provider requests / 5 structurally valid responses** across evolving revisions. This is a small adaptive diagnostic experiment, not a controlled reliability benchmark. Only Exa qualifies for promotion; the 12-case corpus is not 12 regenerated or improved public examples. The remaining creative/dev failures are retained, not manually repaired into apparent model successes.

The configured provider model was `claude-sonnet-5` via the existing Anthropic-compatible configuration; this is the configured identifier, not independent confirmation of the upstream model identity. Every request asked for `max_tokens=3600`. Several provider usage responses report output counts above that request, so 3,600 is a requested ceiling, not a proven billed-token bound. Recorded usage totals are provider-reported and not an independently verified cost. The request/evaluation caps above were enforced. No further model call was made after attempt 9.

Raw replies, original envelopes and all run reports remain in ignored `artifacts/demo-generator-evaluation/`; they contain no API headers or keys. The v3 run is `20261112T084722809080Z`. Its Exa original spec digest is recorded in the [independent final review](demo-generator-final-candidate-review-2026-11-12.md). The published `interaction` object is exactly that model artifact. The server recompiles its legacy narration using the same shared rules used for future generations; this is not a new completion or a manual artifact edit.

## What the failures changed in core

- Catalog links are no longer described as retrieved source passages. Existing attributed excerpts are supplied separately when available; catalog-only grounding stays explicit.
- Complete bounded input combinations, meaningful visible output differences and bilingual nested values are validated on both server and client.
- Short option facts bind entity identity across other controls. Every built-in review patch subset preserves these literal facts. This does not verify semantic truth, undeclared benefits or numeric evidence entailment.
- A repair cannot change a form into an easier editor. It must retain its first parseable supported interaction kind and original task.
- Application code owns operation/boundary narration, so a local table cannot claim that Exa ran a live search and a local form cannot imply downstream email delivery in its surrounding narration.
- Records search includes the current-language source passage. Search, selected-record count, saved set and export now agree; filtering never silently discards an existing selection.
- A registry can withdraw an exact cache key plus spec digest across shipped/cache/reservation paths without blocking the whole product or changing quotas. The old Melius Learning-app → beverage example is withdrawn, while its original JSON remains auditable.

The prompt includes precise facts/cell examples and constraints learned from the real failures. The final repair-kind guard and application narration were verified offline against unchanged replies and regression tests; they were not followed by a tenth paid run. Generated media, arbitrary code execution, conditional formulas, cache simulations and full app generation are outside the four current primitives. Unsupported cases should fail or remain unavailable instead of implying those capabilities.

The evaluator originally read raw crawler records. A production product GET and local ProductService comparison exposed differing normalized fingerprints for Exa. The original reviewed `98e1c153...` key matches production API compatibility; the current JSON-backed product resolves to `af4b2d83...`. Product name, descriptions and source are identical; normalization removes the website trailing slash, changes category `agent` to `other`, and normalizes hardware null to false. Both identify Exa at exa.ai. The release therefore retains the original candidate and promotes the **same spec and interaction**, with metadata-only identity rebinding, to the current normalized key in both backend/crawler mirrors. Original generation time, artifact digest and review metadata are preserved; `identity_rebinding` records the original key and reason. The earlier local preview overlay is no longer required. The evaluator now resolves products through ProductService and saves input identity/context for future evaluations; no extra provider call was made.

## Actual local browser checks

The root agent used the browser, rather than claiming subagents had browser access:

- Production baseline Melius reproduced the Learning-app → bottle/green-tea mismatch.
- Exa candidate: both topics change visible documents; `稀疏`/`sparse` match a passage-only term; exact quote highlighting opens; unrelated terms show an empty state. Unselecting a record changes 3 to 2. Language/branch round trips preserve drafts. The actual downloaded text includes the two selected documents, original evidence, count, disclosure and sources. Reset restores defaults.
- Form and review were tested with explicitly labelled **synthetic local fixtures**, not successful Lovable/Conductor model outputs. Form labels/required fields alter the preview; an empty required form does not submit; valid input shows local-only confirmation. Mouse and keyboard patch acceptance changes the merged text, and reset restores it.
- The rejected Melius candidate was used only to exercise the generic editor locally: edit/include/reorder, tone changes and language round trips preserve the intended draft. Its semantic rejection still stands.
- Hero pause actually sets animation-play-state to paused. Desktop, 390px and 320px layouts were inspected; a 320px product-name split was found and repaired. English-specific CSS removes compressed negative tracking and increases heading/body line-height. Chinese remains separately styled.

These are agent browser and deterministic checks. They do not establish first-time human comprehension, vendor output quality, real search coverage, or the truth of fictional document passages.

## Design sources and Figma

Official references from twelve AI sites and four component libraries were inspected before the design decision. See [component research](demo-components-2026-11-12.md) and the three category audits. These were source/documentation reviews, not claimed hands-on trials of every vendor.

The current [NYU Software Ninjas Design components](https://www.figma.com/design/ShKOiFymrFH8EvIdqTIGHK?node-id=1-351) contain five editable states, actual linked Simple Design System button containers, and the repository's original HorseMark in the icon slot. No separate pause/play glyph remains. The [NYU Make project](https://www.figma.com/make/jB3HVvliW0OtWW1e4N8a37) received the real prototype source, then completed **two actual Make AI prompts** and versions. Root tested horse click/Space, English typography and 320/390 layouts. The first Make version still compressed the English heading; the second corrected it after measured browser feedback. Production adopts the slower scan and depth while retaining its compact layout and existing controls. Exact files, version commits, screenshots and the subsequently exhausted education-plan credit notice are recorded in [the Hero log](hero-motion-2026-11-12.md).

## Automated and deployment checks

- Frontend: 174 tests passed; ESLint and TypeScript passed; catalog contract checked 2,379 records with zero failures.
- Backend/crawler after merging remote main: 737 tests and 11 subtests passed (`pytest tests/ --ignore=tests/test_frontend.py -q`). The ignored file is the legacy localhost:3000 Playwright browser suite, not a backend test; current UI checks are recorded above.
- `next build --webpack` passed after merging remote main. Remote commit and deployment browser receipts are appended after release verification.


## Production cache precedence regression

The first production deployment (`0a4101f`) exposed a second identity issue that local normalized-catalog checks did not reproduce: production compatible keys list the old `424a2fa...` shipped example before the reviewed `98e1c153...` example. Both are shipped files; this was not database-over-shipped precedence. Actual prepared GET and the real page still selected the old record despite the new deployment being READY. Melius withdrawal and the new Hero were already correct.

The shared selector now prioritizes only entries with an explicit nonempty `review_record` and valid ISO `reviewed_at`; among reviewed candidates the later review wins. Generation timestamps do not imply approval. Stable sorting preserves the prior order among unreviewed candidates. Shipped entries still precede database copies, and withdrawal/schema validation remain mandatory with fallback for rejected candidates. No additional Exa cache file or provider request was added. Production-compatible key order, review order, malformed/missing approval, invalid specs and withdrawals are covered by the targeted **93-test passing** suite. The earlier full backend/crawler run remains 737 tests + 11 subtests; the targeted run includes 11 additional precedence regressions.

## Final production verification

- Implementation was pushed non-forcibly after merging remote main. Frontend **READY** at `0a4101f68f78aeedc14edebd7c19eea462dddb9a` (`dpl_AiPr3gmSWmwHZyi95qBCQQN6DvXu`) serves `darkhorseradar.com`. Backend **READY** at cache-priority fix `4217696dfcd454260cc219e61556861b22ca6750` (`dpl_ChjSs1DaQjRbFhE4kvgqv6iMxaY3`) serves `backend-seven-ecru-62.vercel.app`. The frontend deployment for the backend-only fix was correctly skipped by its unchanged-source rule.
- Both backend and frontend prepared GET ultimately returned the reviewed Exa records artifact (`98e1c153...`). The frontend CDN initially retained the previous response; its public 300-second TTL was allowed to expire, then the real page was tested after revalidation. No generation POST was used.
- Production Exa at `/product/36#try-demo`: Transformer / embedding switches show different documents; relevance can change High to Medium; unselecting a row changes 3 to 2; `稀疏` searches the original source passage and its disclosure expands. Export actually downloaded two selected documents B/C with original passages/quotes and source/disclosure text, even though the filter matched unselected A. English/Chinese round trips preserve drafts; no-match search shows an empty table while retaining selections; reset restores three defaults. At 390px document width was 375px.
- Production Melius prepared GET is `not_generated`, and the real page says no prepared example is available. The old learning-app/beverage mismatch no longer displays. The generate button was not clicked.
- Production Hero at 1280px: clicking HorseMark gives `data-running=false` and computed paused animation, Space resumes; cycle 13.5s. English heading tracking is `normal`, summary line-height 28.288px. At 320px the document width is 305px and the horse hit target is 44×44; Kora Systems remains intact. Screenshots are local ignored evidence: `artifacts/hero-motion/production-home-en.png`, `production-home-320.png`, and `artifacts/demo-generator-evaluation/ui/production-exa-mobile.png` / `production-melius-withdrawn.png`.
- CI, Data Verification and CI/CD Pipeline all passed on both `0a4101f` (CI/CD run 151) and the cache-priority fix `4217696` (CI run 140, Data Verification run 133, CI/CD Pipeline run 152).

These deployment and agent-operated checks still do not establish first-visit human comprehension.
