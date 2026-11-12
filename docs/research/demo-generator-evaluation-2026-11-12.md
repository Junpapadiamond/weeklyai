# Demo-generator evaluation design — 2026-11-12

## Decision and scope

The user corrected the approach: improve what the model generates through the shared core, rather than hand-author twelve product exceptions. The three research-product components started earlier in this task are unfinished, unintegrated reference experiments. Do not treat them as generator output or ship them as the solution. This document replaces their implementation plan with evaluation requirements.

This document began as an offline evaluation design against pre-change baseline `c52717a`. The initial browser connection was unavailable. Subsequent authorized provider runs and restored browser verification are recorded in [the run/release report](demo-core-release-2026-11-12.md) and the separate candidate reviews. The design sections below are not assertions that the later experiment did not occur, or that every proposed capability was implemented. First-time comprehension remains unmeasured.

## What the current core can and cannot do

1. **Generation input lacks source passages.** `generate_spec` in `backend/app/services/demo_experiences.py` supplies `name`, `description`, `description_en`, `why_matters`, `categories` and `is_hardware`, each truncated to 1,600 characters. The website/source URLs are allowed citation strings; the generator does not fetch their contents here. A valid source URL therefore does not establish that the generated activity reflects a documented vendor capability. Use existing attributed evidence snippets when available; do not invent them or describe a URL allowlist as factual verification.
2. **The output language restricts the model to preset prose.** The allowed widgets are `choice`, `review`, `compare`, `dial` and a few fixed sample apps. Artifact kinds describe text presentation, not general editable state or computation. An instruction asking for more interactivity cannot make unsupported filtering, model-cell reconciliation or evidence-linked editing work. A small, bounded data-only activity contract and corresponding renderer are necessary.
3. **Dependencies are structural, not semantic.** The validator checks a `when` reference exists and covers earlier options. It does not establish that changing a customer/product/audience changes the relevant output, or that a downstream example describes the same task. Autentic's audience selector passes validation despite never being referenced by later options.
4. **A concrete artifact is required only in selected places.** `_validate_generated_artifacts` checks the first and explicit focus sections; later outputs may remain explanations. Schema-valid JSON can still have meaningless controls or repeated generic text. Structural and behavioral pass rates must be reported separately.
5. **The prompt budget competes with the task.** Current generation has a 2,200-output-token cap, a 90-second shared deadline and at most two attempts. Bilingual input/output examples, datasets and transitions must fit those limits or use a deliberately revised budget. Record truncation and repair rates; do not quietly enlarge all calls or disguise incomplete output as a success.
6. **Old cache wins before generation.** `ready_experience` prefers a product profile, then compatible shipped cache, then shared storage. Prompt edits do not upgrade a ready example. The fingerprint includes version and product facts, not a prompt revision. Core rollout needs an explicit capability/revision policy and read-compatible legacy behavior; visiting an old example must not silently spend a generation credit.
7. **The existing measurement script targets the other pipeline.** `crawler/tools/measure_demo_generation.py` invokes legacy `demo_service.generate`, not current `demo_experiences.generate_spec`. Its schema pass threshold and “switch on” conclusion must not be used as evidence that the new pipeline is useful or ready for release.

## Score each generated activity on five dimensions

Use a 0–3 score per dimension, with a reason and exact JSON/source/state reference. Keep machine checks and reviewer judgments separate. A high total cannot offset a hard failure.

| Dimension | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| **S — Source fit** | Invented capability, unsupported vendor execution, or source does not describe the product's job | Relevant URL only; no attributable capability evidence | Task matches an available attributed product statement; fictional content is identified separately | Exact supporting statement is recorded, limits are respected, and unsupported capabilities are deliberately omitted |
| **I — Input** | No understandable input, or a decorative control | Abstract role/mode labels with no visible task object | Concrete prepared input and controls that correspond to it | Input can be changed in a meaningful supported way, with defaults, bounds and clear empty/invalid states |
| **A — Action** | Fake run/success, nonfunctional control or only acknowledgement | Swaps explanatory paragraphs; user cannot perform the product-relevant local task | A real local operation changes a relevant object (filter, include, edit, reorder, reconcile, simulate) | The operation plus undo/recovery produces a useful inspectable artifact; no vendor execution is implied |
| **O — Visible output** | Generic promise, unrelated result, fake media or completed vendor claim | Plausible but opaque text summary | Concrete passage/table/diff/plan with input-result linkage | First useful result is immediate and later changes are visible, traceable and preserved in export |
| **D — Dependencies** | Contradictory branches, stale result presented as current, missing source reference | References are syntactically valid but necessary context has no effect | All task-defining inputs update/filter affected output; independent edits survive | Every relevant branch, empty state, reset and locale transition is checked, including provenance after edits |

Proposed **candidate gate**, not an observed result: S/I/A/O/D each at least 2; total at least 12/15; every hard check passes. A documented illustration with limited inputs can be useful; do not force every product to attain a 3 through irrelevant widgets. Human comprehension remains a separate gate.

## Hard checks that reject a candidate

- No executable code fields, arbitrary expressions, HTML injection, dynamic network calls, generated script/regex or model-selected package imports. Plain code excerpts remain inert.
- No invented real source URLs, nonexistent source IDs, source passages presented as vendor output, or authoritative claims based on fictional evidence.
- No simulated camera/audio/video playback, real-account connection, deployment, interview, search or measured performance.
- Every offered input combination has a reachable result or named unavailable/empty state; bounded tables/datasets, finite values and allowlisted operators only.
- No cross-entity leakage: audience A's quote cannot substantiate audience B, product A cannot gain product B's ad, and test authorization cannot enable production.
- All state-changing actions have a defined result; exports contain current values, evidence status and sources. Default presets are not completed user work.
- Editing preserves provenance as a reference, never automatically verifies the edited text. A source change must invalidate/update a derived result or clearly mark it for review.
- Viewing/replaying never calls the generator. Runtime content stays local unless a separate explicitly requested generation action is invoked through the existing credit path.

## Adversarial additions for the shared interaction core

These are **offline synthetic probes**, not model-generation results or factual validation. Reproduction payloads are retained in `artifacts/generator-audit/review-records-probes.json`. They were tested directly against Python `validate_interaction` and TypeScript `InteractionSchema` during review; rerun against the final revision because implementation is being updated concurrently. Keep the actual paid-pilot outcomes in their dedicated run/review reports.

| Probe | Why the existing structural criterion is insufficient | Required evaluation assertion |
| --- | --- | --- |
| `records-hidden-only-change` | Two audience variants have identical visible cells, calculation and brief; only the collapsed evidence text changes. Counting any JSON difference as causality lets a selector appear inert. | Compare the default visible artifact, excluding collapsed evidence and decorative copy. A task-defining choice must alter a visible row/cell/group/result, or expose the changed evidence as the primary result. |
| `review-fact-deleted-by-built-in-patch` | A selected fact such as `staging` occurs in the base, but an offered patch changes it to `default`; accepting the model's patch removes the fact. Checking base and patch text as a pooled bag of strings cannot protect the merged result. | Evaluate the actual merged text for every allowed patch subset (at most 16 for four patches), including rejecting all and accepting all. Distinguish deliberate user freeform edits from model-authored patches. |
| `records-composed-measured-claim` | Separate strings `Accuracy` and `%` plus numeric cells `99`, `98` pass a per-string unsafe-copy check, yet the rendered row composes an unsupported performance claim. | Inspect composed labels, values and units as rendered, not only individual strings. Task-fit review must distinguish fictional business quantities from a claim about vendor/model performance; a blanket numeric ban is not a substitute for this judgment. |
| `records-numeric-evidence-mismatch` | A cell contains `120` while its row's source text and literal quote state `12 million USD`. Quote-substring membership passes while the numeric claim has no support from that quote. | Review numerical/entity/period/unit consistency within a row. Preserve original evidence when editing, distinguish edited values from supported originals, and do not call quote membership evidence verification. |

The `facts` contract is **literal binding**, not natural-language fact checking: it can require a selected substring and exclude an unselected substring. It does not establish that the statement is true, that a passage entails a number, that qualifications are preserved, or that the product actually supports a claimed feature. Never label a fact-bound candidate “fact-checked.” Human/source-fit review remains required for those claims.

Additional held-out checks should search for a term occurring only in a source passage, not just its record title; verify that the declared retrieval behavior covers that case or clearly restrict the control to visible table fields. Change numeric values and save the result to ensure the export preserves current values alongside the original evidence without silently presenting an edit as source-supported. These are capability-level tests and must not be implemented as product-ID exceptions.

## Twelve-case fixture matrix

Use the real catalog identity and a frozen evidence packet for each case. This matrix specifies what a **generated data-only spec** must make possible; it is not a request for twelve hardcoded renderers.

| Case | Source packet and task | Input → local action → first visible output | Dependency/negative test |
| --- | --- | --- | --- |
| **Exa** | Retrieval product; attributed vendor description plus explicitly fictional document collection | Chinese/English query → filter/rank and inspect passages → matching source excerpt, optionally collected into notes | `回收电池材料` finds the recovery passage when its authored terms cover it; unrelated query produces no answer; changing query cannot retain a nonexistent selected hit |
| **Daloopa** | Filing-data/model workflow; vendor capability evidence separated from fictional amounts | Period/metric/unit and editable cells → compare to cited sample values → small model table with a visible mismatch | USD thousands/millions convert consistently; Q1 never becomes Q2; invalid or zero denominator does not produce a fabricated growth figure |
| **Autentic** | Interview-and-synthesis capability; authored transcripts with audience IDs | Audience and source selection → include excerpts and edit a theme note → note with exact supporting passages | Changing audience changes available interviews; edited notes are not silently overwritten; removed/changed evidence makes the association explicit |
| **Melius** | Product-ad drafting; no claim of generated media | Product brief and format → assemble/edit campaign fields → matching headline/body/CTA or text storyboard | A learning app never inherits beverage or bottle details; every format preserves the selected product |
| **Sonilo** | Sound-design workflow; text plan only | Fictional scene and sound layers → include/remove editable cues → scene-specific cue sheet | Parkour does not inherit sea waves from a generic ambience choice; disabling a layer removes its rows |
| **Higgsfield** | Vendor-described creative-video job; prepared text sequence | Brief and direction → edit/reorder shot entries → complete shot plan | Reorder changes output/export order; altered direction stays attached to the same product; no footage/play control |
| **Black Forest Labs** | Image-generation product, locally illustrated as a prompt brief | Subject/style/format → assemble and edit prompt → copyable prompt draft | All selected fields appear in the draft; edited draft is preserved or explicitly rebuilt; no nonexistent generated image |
| **GasLab** | Current official availability and music-workflow evidence; concept when capabilities remain unclear | Genre/tempo/section choices → arrange a composition plan → named sections and explicit local duration calculation | Different genre cannot become an unrelated attribution report; no claims of generated audio or measured matching; unavailable capability stays unavailable |
| **Conductor** | Official isolated-workspace/review workflow | Workspace/change selection → inspect and accept/reject an inert patch → before/after plus affected local sample state | Independent changes remain independent; task-list code cannot appear in an unrelated commerce brief; authored checks are not claimed as vendor test runs |
| **Orchids** | Catalog app-builder evidence; detailed announcement unavailable in source review | Feedback requirements and fields → configure a bounded local sample → working feedback board | Owner/priority controls actually change fields; moving a record changes its stage; no fake backend/auth/deployment |
| **Lovable** | Official preview/edit workflow; production example currently absent | Prepared app requirements → bounded UI edit/add/remove → working local preview | Personal/team input changes relevant fields; absent cache does not trigger generation on GET; local sample is not credited to the vendor |
| **Namespace** | Official caching concept, no performance claims | Changed file/dependency version → run fixed cache-key simulation → stage hit/miss trace tied to those inputs | Source edit preserves only valid dependency cache; dependency edit invalidates dependent stages; old trace is marked stale until rerun |

These cases intentionally cover retrieval, structured records, evidence synthesis, content editing, ordering, configuration, patch decisions and deterministic simulations. Reusing a semantic activity primitive across suitable products is desirable. Reusing unrelated task content or decorative controls is not.

## Three research cases as model-generated data

The following are **proposed schema capabilities**, not fields supported by the current validator. Prefer a small discriminated union with runtime behavior owned by the application. The model supplies bounded content/data, labels, defaults and relations; it never supplies algorithms.

### Retrieval collection

- Model data: 3–6 records with stable IDs, bilingual titles/passages, authored term/alias groups, an explicit fictional evidence type, and a default query.
- App primitive: normalize input, match only supported local terms, choose a visible result, inspect its exact passage, include/remove a passage from a collection.
- Relations: `selected_result_id` must belong to current results; collected IDs must belong to the dataset. Source excerpts must remain whole and attributable.
- Evaluation: natural Chinese and English queries, unknown terms, empty query, duplicate inclusion, switching result and changing language. Do not let the model emit executable regex or pretend the keyword matcher is semantic retrieval.

### Source-backed table reconciliation

- Model data: named metrics, periods, reporting currency/scale, numeric source values, document/section references, source passages, and editable initial model values. Include at least one intentional sample mismatch.
- App primitive: typed numeric editing, allowlisted scale conversion, difference calculation, inspection of the referenced passage and explicit adoption of a source value. Optional derived operation comes from an allowlist such as `percent_change`; no formula strings or arbitrary expression execution.
- Relations: each cell references a valid metric/period/source; unit conversion preserves the same amount; a derived operation references exactly the visible cells it uses.
- Evaluation: grouped decimal input, invalid values, zero denominator, negative values if allowed by the declared metric, unit round trip, edited values distinct from source values and export matching the current table. A percentage from declared local arithmetic is a different evidence type from an invented accuracy/performance percentage.

### Evidence-linked research note

- Model data: audience groups, fictional participant IDs and excerpts, short authored theme suggestions and questions, with exact excerpt references.
- App primitive: select an audience, include/remove excerpts, assemble a suggested note from selected entries, edit it, and explicitly rebuild it. The user can inspect all supporting quotes.
- Relations: current passages belong to the selected audience. A user-edited note retains the source snapshot it was written against; changing source selection warns/reviews rather than silently assigning new proof. Per-audience/per-locale edits survive switches.
- Evaluation: every audience leads to different relevant material, contradictory passages can coexist without a fake consensus, no-source state has no suggested finding, manual edits persist, and prior evidence remains accessible until explicitly replaced.

## Experiment protocol

1. **Freeze the evidence and baseline.** Save catalog identity, source URL, dated attributable capability excerpts, current cache key and current spec for the twelve cases. Classify each as available, absent, or legacy; do not count unavailable examples as failed new generations.
2. **Use the real generation entry point.** Evaluate `demo_experiences.generate_spec` or its explicit successor. Bypass ready-cache lookup only inside the evaluation harness; do not force-regenerate public product visits. Stub the provider for offline contract tests.
3. **Offline preflight first.** Validate hand-authored valid/invalid fixtures for every supported activity. Walk all finite choice combinations and declared transition operations. Check bilingual field completeness, reference integrity, empty/invalid states and deterministic results.
4. **Then a bounded model experiment, if separately authorized.** Run each fixture against baseline and proposed generator with the same frozen evidence and model settings. Record first-attempt/repair outcomes, tokens, elapsed time and cost separately. This document does not authorize or run that experiment.
5. **Score blind to condition.** A reviewer scores S/I/A/O/D with excerpts; a second reviewer checks failures and a subset of passes. Disagreement is reported, not averaged away. Model judges may assist, but cannot establish real users' understanding or replace deterministic invariants.
6. **Report denominators.** Distinguish JSON/schema validity, runnable interaction validity, task fit, source support, cache coverage and human comprehension. Show per-case results and worst-category performance; do not collapse them into one success rate.
7. **Promote only the tested capability revision.** Keep legacy replay read-compatible and preserve source/example disclosures. A generated spec may declare its supported activity revision; stale/missing activities must not be silently upgraded by expensive calls on read. Test cache collision/precedence and old-client parsing before publication.

## Proposed result record

```json
{
  "case": "exa-retrieval",
  "catalog_fingerprint": "recorded-by-harness",
  "evidence_packet": "versioned-fixture-id",
  "generator_revision": "candidate-revision",
  "model": "recorded-at-run-time",
  "attempts": 0,
  "schema_pass": null,
  "transition_pass": null,
  "scores": {"source": null, "input": null, "action": null, "output": null, "dependencies": null},
  "hard_failures": [],
  "reviewer_notes": [],
  "tokens": null,
  "cost": null,
  "browser_checked": false,
  "human_comprehension_checked": false
}
```

This template intentionally leaves scores unset. Actual scores and outcomes are in the dated pilot reviews and [run/release report](demo-core-release-2026-11-12.md), not in this proposed result shape.
