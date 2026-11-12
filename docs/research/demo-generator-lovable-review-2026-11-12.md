# Independent review of the first Lovable / Exa provider pilot

Reviewed the provider output and local runtime, not a live vendor product. The provider JSON was not edited. No browser or new provider call was used in this review. References are the saved artifacts and current contract; this is not a human-comprehension study.

## Evidence and outcome

- `artifacts/demo-generator-evaluation/live-report.json`: Lovable validated on its first attempt, 11.56 seconds, two variants, `grounding=catalog_only`; Exa rejected after two attempts, 50.42 seconds. These are recorded run measurements, not independently timed by this reviewer.
- `artifacts/demo-generator-evaluation/lovable.json`: normalized provider artifact, generated at `2026-11-12T08:34:00.765159+00:00`, revision `interaction-v1-2026-11-12`.
- `artifacts/demo-generator-evaluation/exa-raw.json`: both original responses, including fenced JSON. Fences are handled by the existing parser; the defects below are in the contents.
- `frontend-next/src/lib/demo-interaction.ts` and `components/demo/generated-interaction.tsx`: fixed local behavior used for deterministic probes. No product-ID-specific behavior is needed.

**Decision: neither candidate may be published.** Lovable demonstrates useful generation of a bounded interactive form, but does not yet pass semantic release review. Exa is a correct rejection, not a successful example. Neither result establishes general model reliability or that first-time visitors understand the product.

## Lovable task contract and observed behavior

| Dimension | Observation |
| --- | --- |
| Task | Design the fields of a small app form. This is understandable and suitable as one limited example of an app-building workflow. |
| Input | Choose waitlist or feedback; then edit labels, include/exclude fields, change required status and fill the preview. |
| First result | A complete waitlist form is visible immediately. Changing app type replaces the field configuration with a different complete feedback form. |
| Causal change | Waitlist has name/text/required, email/email/required, company/text/optional and team size/number/optional. Feedback has email/email/required, feature/text/required, rating/number/required and comment/text/optional. These are genuine type/required differences, not just headings. |
| Evidence nature | The artifact is model-authored fictional data and a local form. It is not Lovable output and does not demonstrate generated React code, database setup, email delivery or deployment. The runtime states this explicitly. |
| Next action | Follow the supplied official-product link to use the actual service. The saved official homepage URL is a destination; `catalog_only` does not mean official documentation was read for this generation. |

The ordinary task is clear enough for an agent reviewer to explain. The example's breadth is deliberately small. A user could still mistake the example for a generic form builder unless the surrounding product context makes clear that this is one illustrative artifact an app-building workflow might contain. That is an unresolved human-comprehension question, not proof of failure.

### Two release-blocking semantic defects

1. **The rating promises a range the runtime cannot enforce.** Feedback labels its number field `评分1到10 / Rating 1-10`. The contract has no `min` or `max`; the preview accepts finite numbers. A direct probe using the unchanged saved Lovable artifact and the actual TypeScript helper submitted `99` successfully with otherwise valid email and feature values. Therefore schema validity and native `type=number` do not satisfy the displayed promise. The minimal current-contract fix is a generation instruction that labels must not promise constraints the schema does not encode. A later bounded min/max extension would need server, client and tests together; none was added here.

2. **Confirmation invents downstream behavior.** Waitlist says an actual app would record the entry and send confirmation email; feedback says it would store feedback and notify the team. These are unconfigured outcomes. The fixed runtime disclosure prevents an assertion that this local submit actually did that, but does not support the model's prediction of the actual app. Confirmation should describe only the observed local validation/submission, leaving storage, email and notifications to a separate official-product task with appropriate setup/evidence.

Smaller clarity issue found and corrected in the generic runtime: `input_label` is `应用类型 / App type`, already used by the top selector. The first renderer revision reused it as the heading for field configuration. The runtime now supplies its own activity-appropriate titles: `字段配置 / Field configuration` for forms, `编辑草稿 / Edit draft` for editors, and `选择修改 / Choose edits` for reviews. Those titles describe the actual controls; the provider JSON was not patched. This resolves the generic label misuse, not the two semantic release blockers above.

## Exa rejection diagnosis

The final report records `Invalid interaction at interaction.variants[0].artifact.rows[0].cells: expected an object`. Inspection shows several independent failures, so fixing only the first reported path is insufficient.

| Attempt | Structural failures | Semantic failures that remain even after shape repair |
| --- | --- | --- |
| First | Declares news/research options but supplies only news. Text cells are plain strings and include an extra `title_en` key, instead of exact column keys with bilingual Copy values. Evidence uses plain `text`/`quote` plus extra `text_en`/`quote_en` fields. | Invented reporting, real-looking domains and a `40%` speed claim make the fictional sources look verified. `count` is labeled `High Relevance Count` although its declared operation counts selected rows, irrespective of the relevance status. |
| Repair | Supplies both variants and removes the percentage, but text cells and evidence remain plain Chinese strings. Dropping `*_en` did not convert them into `[zh,en]`; the nested bilingual shape is still invalid. | The same count-label mismatch remains. Real-looking publication domains and unverified article claims remain. These are fictional data, but unnecessarily resemble real retrieved evidence. |

The requested user job—search a bounded collection, inspect exact passages and select useful results—is suitable for the records primitive. The failure is not a reason to build an Exa-specific renderer. It shows the prompt needs one concrete nested records example and more precise repair feedback about Copy and cells.

## Minimal prompt improvements to test next

1. State that Copy applies **recursively**, including every text cell and `evidence.text` / `evidence.quote`. Never invent sibling `*_en` keys. Text cell keys must exactly match the declared columns.
2. Include one complete, small records specimen. The following wire-format interaction is a structural example, not a replacement for any saved output and not a special Exa template. The model still chooses the appropriate kind and content for the product.

```json
{
  "kind": "records",
  "input_label": ["示例文档", "Sample documents"],
  "output_label": ["选入的片段", "Selected passages"],
  "inputs": [],
  "variants": [{
    "when": {},
    "brief": ["查找电池回收相关片段并选择要保留的记录。", "Find passages about battery recycling and select records to keep."],
    "artifact": {
      "columns": [
        {"id": "title", "label": ["标题", "Title"], "type": "text"},
        {"id": "topic", "label": ["主题", "Topic"], "type": "text"}
      ],
      "rows": [
        {"id": "a", "cells": {"title": ["文档甲", "Document A"], "topic": ["电池回收", "Battery recycling"]}, "evidence": {"text": ["示例文档介绍电池回收的材料分离步骤。", "The sample document describes material separation in battery recycling."], "quote": ["材料分离步骤", "material separation"]}},
        {"id": "b", "cells": {"title": ["文档乙", "Document B"], "topic": ["仓库导航", "Warehouse navigation"]}, "evidence": {"text": ["示例文档讨论仓库导航中的路径选择。", "The sample document discusses path choices for warehouse navigation."], "quote": ["路径选择", "path choices"]}}
      ],
      "view": "table",
      "calculation": {"op": "count", "label": ["已选记录数", "Selected record count"]}
    }
  }]
}
```

3. Add a short calculation-language rule: `count` always means selected rows, `sum` always means all current row values in its numeric column, and `difference` means its named left row minus right row. Labels must describe that actual behavior. Do not silently imply a conditional status filter.
4. Teach repair with one invalid-to-valid nested fragment: `"title":"中文"` is wrong; `"title":["中文","English"]` is right. Request the complete result again, retaining both locales and all combinations. Do not silently fill missing English in application code.
5. With catalog-only grounding, prefer obviously fictional source identifiers such as `Document A`. Do not generate real-looking news claims, article attributions, benchmark percentages or predicted vendor integrations. Existing surrounding UI supplies the fictional-data disclosure.
6. For form fields, forbid labels promising unsupported bounds or validation. Confirmations should only describe the local sample. This responds directly to the successful-but-semantically-invalid Lovable output.

## Checks performed and limits

- Ran the actual TypeScript `InteractionSchema` against the unchanged normalized Lovable artifact: accepted.
- Used its two real variants with `initialInteractionState`, `changeInteractionInput`, `interactionDraft` and `submitInteractionForm`: type/required configuration changed; `Rating 1-10 = 99` was accepted, establishing the mismatch.
- Read both raw Exa attempts and the final rejection record; did not repair or publish either response.
- The new generic frontend's separate shared-fixture tests cover schema errors, state persistence, live local calculations, patch merging and bilingual static rendering. Those tests do not retroactively validate unsupported claims in provider output.
- No live vendor action, browser walkthrough, external model request, latency benchmarking, or first-time-user test was performed by this reviewer.

Official contextual references used in the earlier research, not claimed as fetched input to this generation: [Lovable preview toolbar](https://docs.lovable.dev/features/preview-toolbar) and [project history](https://docs.lovable.dev/features/projects/history). They support studying editable previews/versioned work; they do not substantiate the sample's email/notification promises.
