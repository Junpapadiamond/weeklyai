# Developer-product demo review — 2026-11-12

## Evidence boundary

This is an official-source and implementation review, not a browser usability test. Browser inventory exposed neither IAB nor a connected Chrome tab. After Chrome was launched, Computer Use stopped because it could not reliably establish the current browser URL; no further UI automation was attempted. No screenshots or live interaction claims are made for this run.

The review uses current repository `c52717a`, read-only production prepared-demo/catalog GETs on 2026-11-12, and current official documentation. No generation POST, paid vendor execution, account creation, or deployment occurred. Agent analysis does not establish first-time visitor comprehension.

## Four official interface references

The following are behaviors described in the vendors' current web documentation. Their rendered UI and account-specific availability were not independently exercised.

| Official product | Source-backed interaction | Useful design inference for our examples |
| --- | --- | --- |
| Cursor | Agent changes appear in a diff view; unwanted edits can be rejected, and a prior checkpoint restores files. [Agent mode](https://cursor.com/help/ai-features/agent) | Show the concrete changed lines beside the affected result; a local accept/reject action should change the sample, rather than merely acknowledge a paragraph. |
| v0 | Design mode selects an element, applies immediate pending tweaks, and supports before/after, undo, reset, and apply. Applied edits become reviewable versions. [Design mode](https://v0.app/docs/design-mode), [Versions](https://v0.app/docs/versions) | Keep the editable preview visible. Separate inspecting an old version, changing a draft, and applying a new version with visible state. A generated progress animation adds no value here. |
| Lovable | The preview toolbar offers element selection, inline text editing, annotation, and comments. Selection supplies context for a requested edit; unfinished changes must be sent or discarded before changing modes. [Preview toolbar](https://docs.lovable.dev/features/preview-toolbar) | Put focused controls beside the selected preview element. A name or field edit must affect that element. Avoid a general prompt box if we only support a few deterministic operations. |
| Replit | App Testing presents actual browser actions while testing, then a recording and section navigation in the task. [App Testing](https://docs.replit.com/features/agent/app-testing) | Show inspectable local checks tied to concrete actions and outcomes. Do not label an authored trace as a vendor test run or simulate a video that never happened. |

These references favor work objects—diffs, selected elements, versions, and test results—over decorative generic icons. Preserve each product's genuine SmartLogo. Use text, selected state, structure, and code notation where they already explain the action; retain icons only where they add a necessary meaning or affordance.

## Four current developer-product reviews

### 1. Conductor — highest priority

- Production: [`p_37eed01228f0e1e2`](https://darkhorseradar.com/product/p_37eed01228f0e1e2?demo=1), prepared GET reports `ready`.
- Current implementation: two sections, project selection and agent-output review. All options contain prepared artifacts and use the generic preset renderer. Source: `backend/data/demos/add6ad0ee87537b11d648958-dcbee5e16ea2f8d4e4785282.json`; `frontend-next/src/components/demo/experience-player.tsx`.
- Concrete defect: choosing e-commerce changes a work-assignment paragraph, while the review options remain task-list React/Express code. No dependency binds those code samples to the selected project. The API excerpt references undefined `title` and does not send a response, while its explanation claims it returns a created task.
- Product-fit gap: the visitor cannot inspect an isolated change, choose what to accept, or observe an integrated result. Reading unrelated snippets does not illustrate managing parallel coding work.
- Official grounding: Conductor describes an isolated workspace per independently reviewable stream, followed by diff review, checks, and integration. It explicitly recommends a shared workspace for frontend/backend changes that must land together; our current mandatory frontend/API/database split oversimplifies this. [Workflow](https://www.conductor.build/docs/concepts/workflow), [Parallel agents](https://www.conductor.build/docs/concepts/parallel-agents).

Proposed contract:

1. **Task:** review two independent changes to a small issue board and decide what enters the local sample.
2. **Input:** select a workspace/change, inspect its before/after code, accept or reject that change.
3. **First result:** an existing board beside a small proposed change, with its affected behavior immediately inspectable; no setup wizard.
4. **Evidence:** deterministic authored patches and local UI state. No agents were run, repository changed, PR opened, or vendor service called. Checks must describe only actual local assertions or clearly authored example outcomes.
5. **Next action:** compare the other workspace, undo a local decision, or visit Conductor's official workflow.

### 2. Orchids 1.0 — high priority

- Production: [`1088`](https://darkhorseradar.com/product/1088?demo=1), prepared GET reports `ready`. Its text cache contains board layouts, data models, stack comparison, and handoff options.
- Actual renderer inferred from current code: `reviewedIds` and `isTextPlan` select `Builder`; this only edits a checklist title and renders the same `exampleSpec('tasks')` app used elsewhere. Sources: `reviewed/catalog/studios.ts`, `reviewed/reviewed-player.tsx:22`, `demo-app-preview.tsx:66`, `lib/live-demo.ts`.
- Product-fit gap: a working checklist is better than text-only output, but the original task concerns a feedback board. Changing the app title does not show how an app builder translates a feature request into a changed interface.
- Official link already recorded by the project: [Orchids 1.0 announcement](https://www.orchids.app/blog/introducing-orchids-1-0). It returned HTTP 503 during this source check; treat detailed Orchids capability claims as unverified. The proposed interaction is an independent app-building illustration, informed by the v0/Lovable references above.

Proposed contract:

1. **Task:** turn a feedback list into a useful triage board.
2. **Input:** add a sample request, choose whether priority/owner fields are visible, and move a request between named stages.
3. **First result:** an already populated feedback board. A feature toggle visibly changes the preview, while moving a request updates stage counts.
4. **Evidence:** authored local app with fictional requests, not generated or deployed by Orchids. Do not expose pretend backend, login, collaboration, or publishing controls.
5. **Next action:** compare the simpler list with the board, reset the sample, or open the official product.

### 3. Namespace — retain the useful interaction, improve explanation

- Production: [`p_a206b05fac257d83`](https://darkhorseradar.com/product/p_a206b05fac257d83?demo=1), prepared GET reports `ready` and selects the reviewed cache activity.
- Source: `reviewed/system-studios.tsx:49`. Build creates keys for dependencies, source compilation, and tests. A second unchanged build reuses all three. Source changes retain dependency cache; dependency changes invalidate every stage.
- Good foundation: the visitor has a real local cause/effect loop. This is not simply a decorative percentage calculator.
- Gaps inferred from code: initial view shows only queued stages/0 hits; source and dependency buttons increment opaque version counters without showing a concrete changed file. After editing inputs, the old trace remains visible with no explicit indication that it belongs to the previous build. A visitor may interpret that stale trace as the new configuration's result.
- Official grounding: Namespace documents caching dependencies and build/test artifacts across invocations. This supports the conceptual distinction; our three-stage cache-key rules are an illustration, not measured Namespace behavior. [Cache volumes](https://namespace.so/blog/zero-latency-caching).

Proposed contract:

1. **Task:** understand why one code change can reuse dependencies while a dependency change requires more work.
2. **Input:** choose an unchanged rebuild, an edit to `src/board.tsx`, or a change to `package-lock.json`, then run a local simulated build.
3. **First result:** show a prepared first-build trace and concrete file inputs. The next run updates stage outcomes and explains each cache hit/miss.
4. **Evidence:** deterministic cache-key simulation; no real build, vendor execution, elapsed-time claim, or speed benchmark. Keep a previous result explicitly associated with its inputs until the next run.
5. **Next action:** compare runs, restore inputs, or inspect official caching documentation.

### 4. Lovable — availability issue precedes redesign

- Production [`948`](https://darkhorseradar.com/product/948?demo=1): prepared GET returned `not_generated`; catalog search returned `demo_ready: false`. A usable prepared live example was therefore not established. No generation was triggered.
- Local source contains curated cache `cf7a3a4c926a0271077b675f-a02b11c202e182d820fcd796.json`. It chooses a task-list brief, opens a generic task app, then changes iteration/handoff text. The preview receives `exampleSpec(step.app_kind)` regardless of brief choice or review choice.
- Gap if this cache is restored: option labels suggest a product decision, but selecting personal versus team scope does not configure a different app. The first visible section is the working preview, so the nominal earlier brief selection is not the cause of that preview.
- Proposed contract: visitor adds a task and makes a concrete UI edit (for example completion display); the visible preview changes and can be restored to a prior local state. Authored/local/not vendor-generated evidence remains explicit. Official docs and availability should be checked before promoting it as ready.
- Do not prioritize another generic checklist until the prepared-data mismatch is understood and the experience has a distinct task from Orchids.

## Recommended implementation order

1. **Conductor:** largest semantic mismatch and an inspectable before/after task that fits the product.
2. **Orchids:** replace the generic renamed checklist with a feedback-board task; preserve simple local scope and truthful evidence labels.
3. **Namespace:** improve its existing causal model with concrete files, cache explanations, and previous-run identity. This can remain smaller than the first two changes.

Lovable's availability is a separate parent-task follow-up. After the combined reference review, implementation was approved for these four specific tasks. Lovable's activity uses a distinct local registration-form builder instead of another checklist:

1. **Task:** turn a small event's registration requirements into a usable form.
2. **Input:** edit the event title and select required email / optional company fields, then apply the draft to the preview.
3. **First result:** an existing registration form that accepts fictional local entries. Applying requirements changes its visible fields and validation; the previous form configuration can be restored.
4. **Evidence:** deterministic local form construction and in-memory entries, not AI generation, vendor output, published registration, or a connected database. No submissions leave the browser.
5. **Next action:** fill the local form, inspect submitted sample entries, restore the prior configuration, or visit Lovable.

## Verification plan after implementation approval

- Verify inputs change the actual visible result, and reset/undo has the stated scope.
- Verify both languages preserve independent edits and selected state.
- Check narrow layout, keyboard operation, accessible labels, and meaningful result announcements in a real browser once browser access is available.
- Test state transitions and task-specific invariants; do not count code execution, source review, or screenshots as human comprehension evidence.
- Preserve SmartLogo and remove only redundant decorative glyphs. Sources, local-example nature, and any actual credit information stay accessible.
