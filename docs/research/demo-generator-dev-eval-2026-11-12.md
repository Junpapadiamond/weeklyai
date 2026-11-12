# Developer demo generation: mechanism and evaluation — 2026-11-12

## Scope correction

The objective is to improve what the model can generate and test that improvement. Product-specific hand-written activities do not achieve that objective. The provisional `product-tasks/developer-tasks.tsx`, `developer-data.ts`, `product-developer.css`, and `developer-tasks.test.ts` files are paused, uncommitted references only. Their nine passing tests establish behavior of those hand-written examples, not generator quality. They should not be registered as product-ID exceptions to satisfy this task.

No external model calls were made in this research. No further browser automation followed the earlier Computer Use stop. Findings below use current source, read-only production GETs, and official documentation; rendered UX and real-user understanding remain unverified.

## Why a better prompt alone is insufficient

Owning sources: `backend/app/services/demo_experiences.py:173`, `backend/app/services/demo_experiences.py:186`, `backend/app/services/demo_contract.py`, `frontend-next/src/lib/demo-experience.ts`, and `frontend-next/src/components/demo/experience-player.tsx`.

1. **The prompt asks for static artifacts.** It explicitly describes inspecting/collecting entries, arranging a sequence, reading inert code, and comparing presets. For parallel coding, it asks for workspace responsibilities, not observable consequences of accepting a change.
2. **The schema cannot encode the desired interaction.** Choices contain label/output/artifact, and `when` can only select a prewritten branch. `app_kind` is fixed to `tasks|timer|expenses`, so a generated app brief cannot configure form fields, a feedback board, or the preview's behavior. Changing a prompt cannot transmit controls the contract strips or rejects.
3. **The runtime ignores app-choice content.** `DemoAppPreview` receives `exampleSpec(step.app_kind)` independent of the option label or earlier brief. The model cannot make the user's selected requirement alter that app.
4. **Validation checks structure and safe representation, not causality.** `_validate_generated_artifacts` verifies the presence of opening/focus artifacts and list entries. The contract validates sizes, safe links, and reference coverage. It does not check that two inputs produce different visible results, that a preview matches the selected project, or that undo preserves unrelated decisions.
5. **The model's factual input is limited.** Generation receives catalog descriptions and allowed URLs, but does not fetch the content of those official URLs in this function. A cited source URL does not establish that a proposed behavior was supported by its contents.
6. **Old caches are a separate axis.** Fingerprints depend on product facts and schema version, not prompt wording. Improving the prompt does not repair existing cache content. Reading old prepared examples must remain free and must not silently start regeneration.

Example observed in production data: Conductor's e-commerce choice still exposes task-list code in the later review section. Lovable's local curated data contains brief choices, but production GET for `948` reported `not_generated` on 2026-11-12. These are distinct semantic and availability issues.

## Smallest useful data-only extension

Add an optional, versioned `interaction` object under the existing experience contract. Keep legacy v2 replay compatible. Dispatch by its declared capability, never product name or product ID. The model supplies bounded fixture data, labels, supported controls, and references; application code owns operations and rendering.

Start with three reusable capabilities rather than a general JavaScript/formula interpreter:

| Capability | Model may supply | Runtime owns | Suitable developer cases |
| --- | --- | --- | --- |
| `records` | Typed fields, 2–8 fictional rows, enum stages, initial view, visible fields, bounded filter/group controls, named changes tied to allowlisted operations | Filter equality, group by enum, show/hide field, edit enum/text values, add a bounded row, accept/reject an independent proposed operation | Feedback board; an issue-list patch review |
| `form` | 1–5 fields of supported types, required flags, title, a bounded configuration draft, initial empty submitted entries | Field rendering, required/email validation, draft/apply/restore, bounded in-memory submission | Registration app; lead-intake or support request form |
| `dependency_graph` | 2–5 named stages, each referencing earlier stages and/or explicit input keys; 2–4 input variants | Acyclic graph validation, canonical equality keys, local cache lookup, run snapshots, reasons for cache hit/miss | Incremental build, document processing, dependency-aware recomputation |

An optional **read-only diff view** can accompany a `records` proposed operation. It is plain text bound to a named operation, not executable code. Applying a rule changes the local fixture through the allowlisted runtime operation. It must never imply that the displayed code ran, a repository was edited, or tests executed. A generated code snippet can still be semantically wrong; require a separate semantic review for the relationship between snippet and operation. If that relationship cannot be established, show a field/value change instead of code.

The first useful state must already exist: a populated board, usable form, or prior run with named inputs. No artificial loading, fake terminal, generic completion bar, or required setup sequence.

### Sketch of a records payload

This is a design outline, not a final schema or an instruction to implement these exact field names:

```json
{
  "interaction": {
    "version": 1,
    "kind": "records",
    "fields": [
      { "id": "title", "type": "text", "label": ["问题", "Issue"] },
      { "id": "priority", "type": "enum", "values": ["high", "normal"], "label": ["优先级", "Priority"] },
      { "id": "resolved", "type": "boolean", "label": ["已解决", "Resolved"] }
    ],
    "records": [
      { "id": "a", "title": ["账单状态错误", "Wrong invoice status"], "priority": "high", "resolved": false },
      { "id": "b", "title": ["导出缺少日期", "Export misses dates"], "priority": "normal", "resolved": false },
      { "id": "c", "title": ["邀请链接错误", "Broken invite link"], "priority": "high", "resolved": true }
    ],
    "changes": [
      { "id": "urgent", "label": ["只看高优先级", "High priority only"], "effect": { "op": "filter_equals", "field": "priority", "value": "high" } },
      { "id": "open", "label": ["隐藏已解决", "Hide resolved"], "effect": { "op": "filter_equals", "field": "resolved", "value": false } }
    ]
  }
}
```

The generated JSON does not contain component names, imports, event-handler source, selectors, arbitrary URLs, expressions, network actions, storage instructions, CSS, or markup. A model-authored `changes` list is not permission to run code.

### Required constraints

- Every control references a declared, type-compatible field or change. Unknown operations, dangling references, duplicated IDs, cycles, overlong data, and invalid initial values fail closed.
- Bound states, rows, fields, and operation counts. Native input values are validated on every transition. User-entered content remains text and is neither interpreted nor sent to a provider.
- `records` filters must demonstrably affect at least one row for the fixture inputs. Form toggles must alter the rendered field/validation contract. Dependency inputs must reach an output stage. Reject controls that only update explanatory prose.
- Keep task data keyed by stable IDs, independent of locale. Locale changes update labels/default copy; they must not erase selections or user edits.
- Output evidence is assigned by the renderer: local computation, authored fixture, or static illustration. Model text cannot promote those to vendor execution or factual verification.
- Optional activity unsupported by the renderer must not be silently dropped while reporting a successful interactive generation. Return a concrete validation failure to the bounded repair call.
- New generation requires either an accepted interaction or an explicitly noninteractive illustration suited to the product. Do not force a calculator or form onto infrastructure/hardware that cannot truthfully be demonstrated this way.

## Four evaluation cases with machine-checkable outcomes

Use the same generator and validators for all cases. Prompts contain the task, a fixed evidence packet, and a bounded fixture. The evaluator's expected outcomes are held outside the model response. Model-authored test cases alone cannot establish a pass.

Each case is scored 0–5: one point per invariant below. A schema-valid answer with only changing prose scores zero on causal criteria. Suggested release bar: at least 4/5 per case, 18/20 overall, and all safety/evidence gates. These are proposed engineering gates, not a measured success rate.

### D1 — isolated code change review (Conductor-like)

**Task/input/result/evidence/next:** review two independent changes to a three-row issue list; accept/reject named changes; observe filtered local rows and selected-change status; read-only illustrative diff/local transformations; undo or inspect the official workflow.

Fixed fixture has one open/high row, one open/normal row, one resolved/high row. Two changes affect priority filtering and resolved visibility.

1. Initial/pending state contains all three rows and neither change is marked adopted.
2. Accepting priority-only leaves the two high-priority rows; an actual row disappears, not just status copy.
3. Accepting hide-resolved additionally leaves only open/high.
4. Reverting priority preserves hide-resolved, leaving the two open rows; the independent decision remains accepted.
5. Rejecting both returns the original three rows. The selected project's rows and diff/change references remain aligned through every transition.

**Semantic review:** are the two units genuinely independently reviewable, and does each code/text diff match its local operation? No claimed git merge or runtime test completion.

### D2 — configurable feedback board (Orchids-like)

**Task/input/result/evidence/next:** configure fields and view for fictional feedback; add/move a row; inspect a working list/board with counts; local in-memory app; change the layout or try the vendor.

1. A complete populated result exists at initial render, with named stages rather than an empty setup wizard.
2. Adding a valid feedback row increases total rows and exactly one stage count by one; blank input is rejected.
3. Moving that row reduces the old stage count and increases the new stage count without duplicating it.
4. Hiding and restoring an optional owner/priority column preserves its values; list/board switching preserves all records.
5. Locale switching keeps row identity, edited values, and stage choices while changing labels/default bilingual text.

**Semantic review:** does the task illustrate app-building through visible configuration rather than merely rebrand a generic checklist? No pretend backend, team sync, or publishing.

### D3 — requirement-driven registration form (Lovable-like)

**Task/input/result/evidence/next:** configure a small event form; change title and required-email/optional-company fields; apply and submit a fictional local entry; local form rendering and validation; restore the prior version or open the official product.

1. Title and field changes stay in a clearly identified draft until applied; applying changes the actual preview.
2. Enabling required email adds an accessible email input and rejects submission without valid email.
3. Disabling email removes that requirement; a valid name-only submission succeeds and contains no hidden email value.
4. Restoring the previous configuration restores its fields and validation while preserving already submitted local entries.
5. User-entered text stays literal, bounded, and stable across language changes; no generation POST or external request occurs on local submission.

**Semantic review:** independent sample construction must not be labeled a real Lovable generation. Production prepared availability is checked separately from renderer quality.

### D4 — dependency-aware rebuild (Namespace-like)

**Task/input/result/evidence/next:** understand recomputation after a file change; choose unchanged/source/dependency input variants and simulate a run; inspect stage results tied to concrete input versions; deterministic graph/cache illustration; compare with the previous run or official caching docs.

1. The initial trace identifies its input versions and is labeled as an authored/simulated run, with no invented timings.
2. Repeating unchanged inputs reuses all stages.
3. Changing only source reuses dependencies but invalidates compilation and tests.
4. Changing dependencies invalidates all downstream stages; restoring an already cached input combination reuses it.
5. Editing next-run inputs does not relabel the previous trace. The trace retains its old input snapshot and displays a pending-change distinction until simulation.

**Semantic review:** stage dependencies must make sense for the task; cache hits are local equality results, not a measured vendor speedup or proof of an actual successful build.

## Evaluation protocol and what not to count

1. Save current prompt/schema revision and current four-case output as baseline only when a bounded model test is separately authorized. This document itself performs no model call.
2. Use official-source evidence packets and equal generation/repair budgets for baseline and candidate. Record initial validity, repair use, final validity, capability selected, and case score separately.
3. Test with a held-out variation: permute record IDs/order, rename the product, alter fixture count, and start in the other language. A renderer dependent on the product ID, a specific label, or a hardcoded three-row count fails transfer.
4. Apply the declared interactions through the generic engine. Snapshot structural outputs—visible record IDs, field definitions, form validation, stage keys—not just changed strings.
5. Reject fabricated execution, unsupported capability claims, and unsafe operations regardless of score. A valid shape is not a fact-check.
6. Report actual generated outcomes and exact failures before altering the prompt again. Do not hand-edit a failed response and count it as model success.
7. Keep curated or manually authored examples separate from generated results. The paused four custom components may suggest invariants, but do not contribute to the generator pass rate.

## Official references used

- [Cursor Agent mode](https://cursor.com/help/ai-features/agent): live edit review, rejecting unwanted changes, and file checkpoints motivate inspectable changes and reversible local decisions.
- [v0 design mode](https://v0.app/docs/design-mode): selected elements, pending edits, before/after, and apply motivate a visible draft/result distinction.
- [Lovable preview toolbar](https://docs.lovable.dev/features/preview-toolbar): element-scoped edits motivate binding requirements to a specific preview object.
- [Replit App Testing](https://docs.replit.com/features/agent/app-testing): inspectable browser test evidence motivates explicit evidence classes; our local fixtures are not such tests.
- [Conductor parallel agents](https://www.conductor.build/docs/concepts/parallel-agents): independent workspaces and shared-state collaboration must be distinguished instead of splitting every frontend/API/database task mechanically.
- [Namespace cache volumes](https://namespace.so/blog/zero-latency-caching): artifact/dependency reuse grounds the cache concept, without establishing performance of our sample.
