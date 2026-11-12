# Final pilot candidates: independent release review

Date: 2026-11-12. Run: `artifacts/demo-generator-evaluation/runs/20261112T084722809080Z`. Generator revision: `interaction-v3-2026-11-12`.

**Recommendation:** reject Melius; conditionally accept Exa as a local fictional document-selection illustration after the generic search/narration checks below; reject Conductor. Do not report this as three successful product demos. No candidate in this report establishes vendor output quality or first-time visitor comprehension.

## Method and receipts

Reviewed each raw completion and available normalized JSON. A local replay expanded the last Melius and Exa responses through the actual compact decoder and validator and confirmed that their `interaction` objects exactly match the saved candidates. No artifact text was manually repaired by this reviewer. Conductor has raw responses but no accepted normalized candidate.

| Product | Attempts | Recorded time | Structural result | Spec SHA-256 recorded by evaluator |
| --- | --- | --- | --- | --- |
| Melius | 2 | 30.56 s | Editor; 4 complete variants | `876c74fd83308e9cc4eff567717ddaa63bdd14519411dc273392da853f6c709a` |
| Exa | 2 | 46.95 s | Records; 2 complete variants | `6c58af593fa990e63781887662b7a9955567bd71f27ab464909cebcc63cfbc0e` |
| Conductor | 2 | 80.55 s | Rejected: patch anchor absent from original base | No accepted spec |

This reviewer made no provider request. The original source packet, run revision, attempts, raw responses and original candidate hashes must remain attached to evaluation results. Server-owned narration may change a later normalized envelope; it must not silently overwrite the original evaluation receipt or be described as a new model completion. The generated `interaction` artifact can remain byte-for-byte unchanged while application narration accurately describes its local operations.

The S/I/A/O/D rubric is defined in [the evaluation design](demo-generator-evaluation-2026-11-12.md): each dimension must score at least 2, total at least 12/15, and every hard check must pass. Scores below are source/data/runtime judgments. Actual-page verification is being performed separately by the parent agent; this report contains no new browser or human-observation evidence.

## Melius — reject

| S | I | A | O | D | Total |
| --- | --- | --- | --- | --- | --- |
| 2 | 2 | 3 | 2 | 2 | **11/15** |

- **S, source fit 2:** editable campaign drafts fit the broad creative-production job described by [Melius](https://www.melius.com/). The actual supplied stored excerpts concern funding, founders and revenue, so their presence does not ground detailed creative-workflow claims. The sample is an independent drafting illustration.
- **I, input 2:** the selected subject is now concrete: FitFlow/workout tracking app or ZenBrew/natural herbal tea, with a separate motivational/lifestyle tone. These facts appear in each relevant artifact.
- **A, action 3:** the generic editor supports changing real copy, field inclusion, ordering, reset and export. This is a genuine local drafting operation, not media generation.
- **O, output 2:** the fields contain usable headline, two bodies and CTA, but the copy cannot be fully traced to the supplied brief. The scenario promises three tone variations while there are two tone options and two body fields, so its description does not match the task structure.
- **D, dependency 2:** changing tone now retains FitFlow or ZenBrew; the previous cross-product substitution is fixed. Literal facts and coherent visible branches pass, but preservation of all undeclared product assumptions is not demonstrated.

Remaining semantic blockers are substantive. FitFlow's lifestyle body adds smart reminders that are absent from the selected brief/facts. ZenBrew's motivational copy promises energy, focus, morning clarity and rest, also absent from the declared input. Broad fictional-example disclosure does not demonstrate faithful drafting from a constrained product brief. Names remain stable, but a stable name alone cannot justify invented features or benefits.

The current candidate is improved over the first pilot, but it does not meet the 12-point candidate gate. App-owned operation narration can remove the claim that the user is currently inside the Melius editor; it cannot fix these artifact-content weaknesses. Do not hand-edit this candidate into a model success. Retain it as an evaluation result and improve the general prompt/source packet before a later authorized generation.

## Exa — conditional candidate pass, not a live-search demo

Provisional score after the two generic corrections below:

| S | I | A | O | D | Total |
| --- | --- | --- | --- | --- | --- |
| 2 | 2 | 3 | 3 | 2 | **12/15** |

**S, source fit 2.** The official [Exa product page](https://exa.ai/), retrieved for this review, describes search for AI agents and relevant content excerpts/highlights. Selecting documents and inspecting their passages is aligned with that job. The generation itself was `catalog_only`; the independent source review must not be relabelled as evidence the model received. The fictional technical passages and qualitative relevance choices are not real Exa search results, scientific findings or retrieval benchmarks.

**I, input 2.** Two prepared topics, Transformer optimization and vector embeddings, each have three specific document records. This is a concrete collection to work on, with an additional local text filter; it is not arbitrary semantic web search.

**A, action 3.** The supported task is to filter the collection, inspect a literal supporting passage, change a local relevance judgment, select records, observe the selected-record count, reset and save the current set. These operations change a relevant object. A clear local-example disclosure and application-owned narration must remain adjacent to them.

**O, output 3.** The first result is a real table of prepared document titles/relevance values, with inspectable fictional passages and exact quote highlights. The two topics change visible records, not only hidden evidence. Current selection and evidence are carried into the export. The candidate contains no playable-media affordance, fabricated live search log or numerical retrieval-performance claim.

**D, dependencies 2.** Both topic branches are internally consistent, all references/quotes resolve, and the shared runtime has explicit per-variant/per-language drafts and reset behavior. This reviewer has not independently completed the actual Exa page's keyboard/mobile/locale/export session, so D is not elevated to 3.

### Conditions before promotion

1. **Search must match its stated scope.** At review time, `visibleInteractionRows` searched only visible cell text. Searching `sparse` or `稀疏` would miss the relevant attention document because those terms occur only in its evidence. The parent assigned the generic records runtime to include evidence text/quote. Verify both terms find the attention record, an unrelated term yields the explicit empty state, and clearing the filter restores the collection. Keep the control framed as local record search; do not imply semantic retrieval or a vendor query.
2. **Application-owned narration must describe application-owned operations.** The raw scenario says Exa returns documents during the current activity. The parent's planned generic narration derived from `kind` is the correct repair: a local prepared collection is filtered/selected; the actual vendor has not run. This is a shared server/runtime correction, not hand-editing Exa's generated artifact. Verify the v2 compatibility snapshot and exports retain the same boundary.
3. **Verify the real page.** Confirm both topics, source-only queries, empty state, relevance edits, selection/count, independent language drafts, reset and current-value export. Until that result is recorded, the release verdict remains conditional.

### Limitations that remain after those conditions

The dataset is only six fictional records across two topics. Literal filtering does not reproduce Exa's search ranking, coverage or understanding of arbitrary queries. Relevance is a local editable judgment, not a measured vendor score. The scientific text includes expressions such as research shows; its disclosure must remain unambiguous, and it should not be reused as a factual technical reference. Source links establish Exa's product direction, not these made-up documents. No real-user comprehension or vendor-quality claim is permitted.

The first raw attempt contained numerical accuracy/computation percentages; the validator rejected it. The repaired response retained the records task and removed those claims. That is a successful bounded structural repair, not proof that every remaining natural-language assertion is fact-checked.

## Conductor — reject, exact anchor failure

| S | I | A | O | D | Total |
| --- | --- | --- | --- | --- | --- |
| 2 | 1 | 0 | 0 | 0 | **3/15** |

The broad review task fits Conductor's documented workflow. Its official [workflow](https://www.conductor.build/docs/concepts/workflow) and [parallel-agent guidance](https://www.conductor.build/docs/concepts/parallel-agents), retrieved for this review, distinguish independent workspaces from shared work and require review/integration of changes. This candidate instead proposes dependent edits as independently selectable patches against a base that does not contain their targets.

Actual anchor counts, checked directly in both languages:

| Attempt / branch | Patch | Occurrences in original base | Where its target really occurs |
| --- | --- | --- | --- |
| 1 / auth | `validation` | 0 | `login_route.after` |
| 1 / export | `batch` | 0 | `csv_endpoint.after` |
| 2 / auth | `store` | 0 | `login.after` |
| 2 / export | `batch` | 0 | `csv_route.after` |
| 2 / export | `headers` | 0 | `csv_route.after` |

For example, attempt 2's `store.before` is:

```python
    if username:
        return jsonify({'token': 'abc123', 'username': username})
```

The original base contains only Flask imports, app initialization, a health route and the run guard. That login code exists only in another patch's replacement. Accept/reject combinations therefore cannot be merged independently against one immutable base. The validator correctly rejects the exact path `interaction.variants[0].artifact.patches[2].before.zh` on both attempts. No normalized candidate was published by the evaluator.

There are additional quality concerns in the raw text: static authentication tokens, development secrets, and a session patch that duplicates application initialization. These snippets are inert and were not executed; they still make a poor illustrative code-review task. The proper next experiment is a smaller existing baseline with two genuinely independent edits, preferably ordinary formatting/filtering logic rather than fabricated authentication. The model must choose every patch anchor from that same original base and preserve selected facts for every patch subset. Do not patch the failed JSON by hand or weaken the anchor validator.

## Historical Melius cache — exact-spec withdrawal implemented

The known misleading shipped entry is:

| Property | Value |
| --- | --- |
| File | `backend/data/demos/2561dcea0804ca1875e3e6d5-a28f9e5f9a8c828ad69f68d9.json` |
| Cache key | `2561dcea0804ca1875e3e6d5-a28f9e5f9a8c828ad69f68d9` |
| Product key | `2561dcea0804ca1875e3e6d5` |
| Product ID | `p_85288867790377a1` |
| Origin / generated at | `pregenerated` / `2026-10-16T22:09:11.829814+00:00` |
| Canonical compact spec SHA-256 | `145ff735b348b1cab707344dc5e73ea2ba3ec175ab7f5c4b7bb670d6e244ffd1` |
| Evaluation-style spec SHA-256 | `b1ac91cdeee6c2d464f8267f045ae9e67fc7ce9f259906a706c2c22f8a16d713` |

The compact digest is computed from UTF-8 `json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(',', ':'))`. The evaluation-style digest uses the existing evaluator's default separators. Do not compare one serialization's digest against the other.

A current read-only local `ready_experience` call selected this exact cache key. It has a `brief` choice for Health beverage or Learning app, followed by a `format` choice with no dependency. Both format artifacts contain beverage/bottle/green-tea content. Choosing Learning app therefore leaves a downstream drink advertisement. This is a confirmed content contradiction, not merely a missing new interaction feature. This local check does not independently establish the current production deployment's response.

The generic registry `backend/data/demo_withdrawals.json` is keyed by **cache key plus exact spec digest**, with a reason pointing to this review. Its helper applies to shipped entries, curated/store candidates and cached reservation responses, so an identical database copy cannot resurrect the bad example. A later different spec for the same key remains eligible for the normal validation and review process. The rejected source JSON is retained for audit and has not been replaced with hand-authored model output.

Withdrawal leaves the product and official link available and makes this prepared-example state `not_generated`. Neither GET nor catalog reads auto-generate or spend credits. Explicit future generation still follows normal reservations and cannot replay the withdrawn cached payload. No quota/counter algorithm changed: an explicit new reservation uses the existing charge/refund behavior, while cached replacement reads remain free.

The dedicated regression suite covers SQLite and Mongo store reads, key listings, reservations, free replacement replay, exhausted budgets, both GET routes and ready catalog filtering. It verifies that timestamps and other envelope metadata do not change the digest match, a changed spec for the same key remains eligible, registry edits invalidate the published cache, a withdrawn curated profile is not advertised as ready, and the original JSON and persisted audit copy remain intact. These are local automated checks; production propagation and real-user comprehension are not established by them.

## Repair integrity change completed

`generate_spec` now remembers the first parseable supported interaction kind. A repair that changes a form task into an editor is rejected even if the editor would independently validate. The repair prompt explicitly preserves the original user task and operations. The regression covers invalid-form → valid-editor rejection and invalid-form → repaired-form success. The targeted generation/core plus existing artifact suite passed 50 tests with provider calls mocked.

This guard preserves the chosen primitive; it cannot prove that a repaired draft still serves the same semantic task. The release review above remains necessary.
