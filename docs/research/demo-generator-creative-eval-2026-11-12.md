# Creative demo generation: contract and evaluation

Date: 2026-11-12. Scope: generator and data-only runtime design, following the user's correction that improvements must come from better model generation rather than hand-built product exceptions.

## Status and evidence boundary

The product-specific implementation was stopped. Only `frontend-next/src/components/demo/product-tasks/creative-data.ts` had been added; it is not imported or connected to a renderer. There is no creative task TSX, CSS or test implementation. Its authored examples are research material, not a proposed production exception list. The selected static-editor plan in [the earlier audit](demo-audit-creative-2026-11-12.md) is superseded by this generator-focused direction.

This review uses the current generator, validator, frontend data contract and committed examples. It includes a local, network-free replay of five examples through the existing Python validator. It does not include a new model completion, provider expense, browser session, screenshot, or human comprehension test. The eight official vendor references and their observation limits remain in the earlier audit. In particular, [Melius](https://www.melius.com/) describes connected creative inputs/outputs, [Sonilo](https://sonilo.com/) describes video-conditioned sound, and [GasLab](https://gaslab.ai/) currently advertises an upcoming opening and guest list; these distinctions must reach generation context.

## What the current system can and cannot express

| Owner | Observed behavior | Consequence |
| --- | --- | --- |
| `backend/app/services/demo_experiences.py::generate_spec` | The prompt already asks for concrete artifacts, meaningful choices and consistent dependencies. It also asks for independent sections and gives a `steps/options` shape. | More prose instructions alone cannot supply missing runtime capabilities. The output shape still encourages separately authored paragraphs. |
| Same generator | The context contains name, description, English description, why-matters, categories and hardware flag; the two source URLs are an allowlist, not retrieved source passages. | A source link does not establish that the model saw current availability or a precise vendor workflow. GasLab's current guest-list status is absent unless present in catalog copy. |
| Same generator | `MAX_OUTPUT_TOKENS = 2200`; two bounded attempts share a 90-second deadline. | Four or more fully duplicated bilingual branches may exceed the existing budget. Compact bindings and small branch counts matter. No budget increase is justified without measurement. |
| `demo_contract.py::validate_experience` | `when` can reference one earlier step; at most four options exist per step. Validation checks dependency coverage, not the semantic relation of artifacts. | It cannot directly express multiple independent inputs determining one artifact. A missing `when` makes unrelated downstream content valid. |
| `demo_experiences.py::_validate_generated_artifacts` | New output must have first-step/focus artifacts and actual list/sequence items. | This proves inspectable content exists, not that inputs change that content correctly or produce editable work. |
| `frontend-next/src/lib/demo-presentation.ts::selectExperienceChoice` | Dependency-aware selection already resets affected branches and preserves independent choices. | Correct declarative dependencies can work; the cache data often does not declare any. Do not replace this with a product-ID switch. |
| `frontend-next/src/lib/demo-notes.ts::ItemDraft` | Draft state records order and picked entries only. | Existing generated artifacts cannot express editing the actual text or binding a user-entered subject into a prompt. |
| `ExperienceArtifact` / `PresetPlayer` | The renderer shows static artifact input/output and optional item order/notes. | A visitor can inspect examples, but it cannot currently behave as a coherent prompt, script or cue-sheet editor. |
| `ready_experience` / `fingerprint` | Curated profiles precede shipped cache and store results; cache identity includes contract version and catalog facts, not prompt revision. | A prompt improvement does not repair existing examples. Replaying old cached data must not be reported as evidence of new generation quality. |

### Local replay results

Executed `demo_contract.py` with `runpy.run_path`, loaded each committed JSON, and called its actual `validate_experience`. No service/provider call was made.

| Example | Accepted by current contract | Sections / option counts | Options with `when` | Artifacts |
| --- | --- | --- | --- | --- |
| Melius | Yes | 2 / 2, 2 | 0 | 4 |
| Sonilo | Yes | 3 / 3, 2, 1 | 0 | 5 |
| Black Forest Labs | Yes | 4 / 2, 2, 2, 2 | 0 | 0 |
| GasLab | Yes | 2 / 2, 1 | 0 | 3 |
| Higgsfield curated profile | Yes | 4 / 2, 2, 2, 2 | 0 | 8 |

The actual accepted Melius data has beverage text in both later format options, including when the earlier choice is Learning app. The accepted GasLab data offers Ambient Electronic, followed by a fixed attribution input describing an 8-bar techno segment. These are concrete examples of structural success with task failure. The replay did not call the stricter generation-only validator; Black Forest Labs is a legacy record without first-value artifacts.

## Proposed minimum model-output contract

Add a versioned, optional task payload to the existing data-only envelope. Keep old v2 replay intact. The shared runtime chooses presentation from artifact kind and capabilities, never product name, product ID or website. The model supplies the task's content and relationships; application code supplies the small set of safe operations.

1. **Inputs:** stable IDs, bilingual label, native control kind, bounded initial value. Start with `select`, `text` and `toggle`; each select option has a stable ID, short label and optional longer value for literal inclusion in the output. Text inputs are literal drafting fields, not a promise of live AI transformation.
2. **Variants:** stable ID, equality conditions over named finite select inputs, and an artifact. A variant may depend on several inputs. Each reachable combination must resolve to exactly one variant; reject overlaps and gaps. Keep at most two semantic select inputs and eight variants for the first generator iteration. Prefer bindings to repeated prose where the transformation is literal composition.
3. **Artifact:** `text`, `list` or `sequence`, with stable field/item IDs, bilingual labels and content. Text content is a sequence of literal-copy or input-reference parts, not code or a model-supplied expression. Fields/items may be editable. Sequence supports reorder; a list does not acquire arbitrary sequencing controls. A row may be included by a named toggle.
4. **Evidence and next action:** server-owned independent/prepared status, cited source reference, and an availability-aware official action. A draft is an editable text artifact, never proof of generated media. The source URL stays out of template evaluation.

The following is a **contract sketch**, not code accepted by the current schema. It shows that product and format jointly select one actual draft while a subject can be inserted literally:

```json
{
  "task": {
    "schema": "draft-task-v1",
    "inputs": [
      {"id":"product","kind":"select","label":["产品","Product"],"initial":"app",
       "options":[{"id":"app","label":["口语应用","Speaking app"]},{"id":"tea","label":["青茶饮品","Green tea"]}]},
      {"id":"format","kind":"select","label":["格式","Format"],"initial":"copy",
       "options":[{"id":"copy","label":["广告文案","Ad copy"]},{"id":"script","label":["分镜脚本","Shot script"]}]},
      {"id":"name","kind":"text","label":["名称","Name"],"initial":["口语伙伴","Speaking partner"],"max_length":60}
    ],
    "variants": [
      {"id":"app-copy","when":{"product":"app","format":"copy"},"artifact":{
        "kind":"text","fields":[
          {"id":"headline","label":["标题","Headline"],"editable":true,"parts":[
            {"input":"name"},{"copy":["：下一次开口，先练一遍",": rehearse your next conversation"]}]},
          {"id":"body","label":["正文","Body"],"editable":true,"parts":[
            {"copy":["从点餐到问路，把旅行对话变成每天的口语练习。","From ordering food to asking directions, turn travel conversations into speaking practice."]}]}
        ]}}
    ]
  }
}
```

The sketch deliberately contains only one branch. A real generated payload must include the other three reachable branches or fail validation. This is an important difference from accepting incomplete output and silently falling back to the first example.

### Keep the first core small

- Melius needs four complete prepared branches for two products × two formats. All editable fields belong to the selected branch.
- Sonilo needs three scene variants with three scene-specific rows. Music/ambience/effects toggles include those rows; no additional eight-way variant expansion is needed.
- BFL can use one prompt artifact whose parts refer to subject, selected style value and selected framing value. A model supplies the actual composition wording. A generic binding renderer assembles it.
- Higgsfield needs two direction variants with a product-name reference and placement value. Its three items are editable and reorderable. There is no fake image/video element.
- GasLab needs two genre variants with editable arrangement rows. A tempo may be a literal brief input. Do not add arbitrary formulas to this first core just to emulate the abandoned dedicated editor. If calculated duration becomes a shared requirement, add a separately specified, bounded arithmetic operator with finite/zero/unit tests; label the result local arithmetic.

This is a reusable authoring grammar, not a universal visual funnel. A prompt editor, cue sheet and ordered shot plan still present different artifacts. The model should omit controls that cannot cause a useful output change.

## Runtime and validation obligations

**Selection and binding:** validate IDs/references before rendering. Resolve variants from finite select values; interpolate only literal strings. Never evaluate expressions, HTML, URLs, function names or model-authored event handlers. An unknown reference, unresolved variant or unsupported operator is an error, not a silent fallback. Use the same resolver to form the visible artifact and downloaded text.

**Edits:** store overrides by specification identity, variant ID, field/item ID, language and the relevant bound-input context. Changing a dependent input selects that context's prepared text; returning restores its edits. Independent fields retain edits. Store ordered stable item IDs rather than positional indices. Locale switches preserve controls and order, with separate Chinese and English text drafts. Reset affects this task only. Empty user text remains empty and gets an honest empty state; it must not silently turn back into the prepared draft.

**Operational truth:** changing a local input must not reserve credits, call the provider, claim a vendor action, or imply that a local text transformation generated audio/video/image. A real generation request remains an explicit separate action. Saving exports actual visible edited content, chosen inputs, source, example status and provenance; it cannot claim untouched defaults were user-completed work.

**Coverage checks:** enumerate bounded finite select combinations and require one matching variant. Assert every input is used by a condition, binding or row inclusion. For each finite choice, compare the resulting artifact bodies in relevant contexts, ignoring control labels and headings, and flag exact no-op alternatives. References and output differences prove dependency behavior, not full semantic correctness; a generic validator cannot prove that beverage claims belong to an app.

**Source grounding:** pass a bounded, explicitly attributed evidence bundle to the model when available: catalog fact, official excerpt, source URL and retrieval date/status. Mark retrieved content as untrusted data. An allowed URL alone is not an excerpt. If current availability is absent, use a neutral official-link action rather than inventing a free trial or launch status. GasLab's researched status can form a known evaluation fixture; general generation must not infer availability from its name.

**Generation and repair:** ask the model to choose one visitor task, artifact type, small input set and complete branch map before writing compact copy. Keep the five task-contract answers in the planning requirement rather than repeating five subtitles in the interface. Repair messages should name the failing path/combination or unknown binding and request a complete corrected object. Keep the existing bounded attempts, timeout, refunds and no-fabricated-fallback behavior.

**Compatibility:** do not globally invalidate old v2 caches merely to introduce the optional task payload. Record generator/contract revision in new results and evaluation manifests. Existing incorrect examples need explicit corrected generation and review; adding a new renderer cannot make their unrelated prose coherent. Old prepared examples remain labelled as prepared examples until replaced, and their GET route remains read-only.

## Five acceptance cases

These cases evaluate the **model's new data plus the generic runtime**, not hand-authored product components.

| Case | Input and required visible result | Negative mutation / failure to catch | Next-action and evidence checks |
| --- | --- | --- | --- |
| Melius | Choose speaking app, then both copy/script. Every resulting body and shot concerns speaking practice. Switch to tea and back; each branch restores its own edits. | Replace app script with the tea script; omit product from conditions; make both formats the same artifact. This must fail a case-specific semantic or structural check. | Independent prepared ad draft; no rendered ad claim. Official Melius link. |
| Sonilo | Choose parkour, enable ambience/effects and disable music. Cue rows concern city/run/vault/landing; inactive music row is absent from visible result and export. Switch beach and back. | Copy beach waves into parkour ambience; toggle only changes button styling; export still includes disabled rows. | Cue sheet with proposed timing, no audio player, waveform or licensing claim. Official Sonilo link. |
| BFL | Enter a distinctive subject string, choose illustration and wide. Prompt contains that literal subject and meaningful illustration/16:9 composition instructions. Editing the prompt changes the export. | Subject appears only in the form; output says Configured; new format changes its label but leaves square composition; markup-like input is interpreted as HTML. | Prompt draft, no generated image; BFL official link. Empty subject has an explicit empty state. |
| GasLab | Select ambient. Arrangement descriptions are pad/texture-based and all refer to that plan; editable sections survive locale toggles. | Ambient route emits a techno attribution report; claims to detect training artists; action promises immediate generation despite supplied coming-soon evidence. | Composition plan, no generated audio or authorship proof; availability/guest-list action from supplied source context. |
| Higgsfield | Change product name, choose close-ups and product-page placement. All three shots retain the name and chosen treatment. Reorder and edit shots; export matches their visible order/text. | Direction changes only explanatory copy; a different product leaks into a shot; reorder resets locale drafts; unavailable footage gains a play button. | Production plan, no rendered video. Official Higgsfield link. |

Common checks run in both languages: initial useful artifact, unknown-binding rejection, every finite combination resolves, no decorative/no-op choice, locale round-trip, edits restored on context round-trip, reset, read-only entry, export consistency and bounded plain text. Browser keyboard/mobile verification and a first-time human comprehension session remain separate gates.

## Evaluation sequence and reporting

1. Establish the five current failures above as baseline fixtures. The local replay already establishes that existing structural validation admits them.
2. Implement generic validator/resolver tests using compact fixtures, including missing/overlapping variants, stale dependencies, HTML-like literal input, disabled rows and edited export. These tests need no model or network.
3. Run the new prompt against the five source-grounded creative cases under an explicitly bounded generation evaluation. This review did **not** run that stage. Record model/provider identifier, prompt revision, source snapshot, attempt count, raw completion hash, validation/repair outcome, tokens and latency; redact secrets.
4. Score generated content with the case-specific invariants above. Separate JSON validity, causal behavior, artifact usefulness and source/claim accuracy. Do not collapse them into one pass rate. Human review is required for semantic contradictions that exact checks miss.
5. Include at least two previously unseen creative products as held-out cases, with no product-specific runtime branches. Test multiple generations before claiming a stable improvement. Increasing token budget or adding model review should follow observed failures and cost data, not precede them.
6. After automated checks, verify the actual page and ask first-time visitors what changed and what they can use. Record their answer; agent or structural approval is not a comprehension result.

No current claim is made that the proposed contract has been implemented or that model quality has improved. The result of this review is a reproducible baseline failure and a bounded, general repair target.
