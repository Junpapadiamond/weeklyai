# Research and operations examples — 2026-11-12

**Implementation direction superseded:** after the initial greenlight, the user requested a shared model-generation improvement rather than product-specific static implementations. The findings and task contracts below remain evaluation inputs. The unfinished standalone research components are unintegrated references, not the chosen delivery. See [demo-generator-evaluation-2026-11-12.md](demo-generator-evaluation-2026-11-12.md) for the current evaluation plan.

## Evidence limits

This review uses current source, current bundled examples, public read-only prepared-example API responses, and official vendor webpages. It is **not** a browser walkthrough. The in-app browser was unavailable; the native fallback stopped because the tool could not safely determine the browser URL. No further computer interaction was attempted. No screenshots or human-comprehension findings are claimed.

The user asked to study professional references before implementation. The four official references below were read before the implementation greenlight. The main task combined these with the other agents' references, then authorized Exa, Daloopa and Autentic work. Decorative generic icons are unnecessary here: content, document references, a table and passage selection can express these tasks. Product identity continues to use the shared real-logo component.

## Four official references

| Reference read | What the official content describes | Borrow for this project | Do not copy or claim |
| --- | --- | --- | --- |
| [Perplexity Pro Search](https://www.perplexity.ai/help-center/en/articles/10352903-what-is-pro-search) | A question leads to a source-linked answer; follow-up questions refine the work. | Keep the input and evidence visible together, with a clear unsupported/no-match state. | Do not imitate a live web search, model run, or research confidence using a local fixed collection. |
| [Notion AI](https://www.notion.com/product/ai) and [Enterprise Search help](https://www.notion.com/help/enterprise-search) | A question can be scoped to selected sources or pages; retrieved workspace answers cite their sources. | Make the chosen collection explicit and keep that scope attached to the result. | Do not show fake connected apps, private workspace access, or a decorative universal prompt box. |
| [Glean](https://www.glean.com/) and [Citations help](https://docs.glean.com/user-guide/assistant/glean-chat/glean-chat-citations/glean-citations) | Inline source markers lead to context previews and, where supported, the exact supporting passage. | Open a specific supporting passage from a result or model cell. | A citation is a route to evidence, not a claim that a user edit is verified. Do not invent real source links for fictional data. |
| [Granola](https://www.granola.ai/) and [its official note workflow](https://www.granola.ai/blog/how-to-use-granola-with-zoom) | Rough user notes and a transcript contribute to a structured summary; templates affect organization. | Let users choose source passages and build an editable synthesis while retaining the original text. | Do not pretend to record audio, conduct an interview, or run Granola. Avoid filling a summary with unsupported generic prose. |

These are documentation-grounded interaction patterns. Their visual appearance, responsive behavior and actual session performance were not observed in this run.

## Current product audit

Public GETs to `/api/v1/demos/prepared/36`, `/7`, `/1056` and `/p_1b6f5ea8f77f3c28` returned `ready`, with keys matching the current bundled Exa, Daloopa, Abridge and Autentic examples. Exa, Daloopa and Abridge satisfy the text-only gate in `experience-player.tsx` and use the reviewed renderer. Autentic has artifacts and uses the preset renderer. A fifth check, Granter `p_35d86b7001bf3f1b`, returned `not_generated`; no generation request was made.

| Product | Actual input/output from source | Observable code behavior | Assessment |
| --- | --- | --- | --- |
| Exa / `36` | Keyword input over three fictional documents → matching title and paragraph | `record-tasks.tsx:24` splits only on whitespace, scores substring hits and displays any positive hit. Directly running the same algorithm: `电池 回收` ranks the recovery manual first; `回收电池材料` returns no result. | A natural Chinese query fails although the material is present. Source inspection is only an expanded paragraph; users cannot collect evidence into a research artifact. |
| Daloopa / `7` | Select three filing lines → independent editable text areas | `catalog/records.ts:43` supplies periods and units in labels. The generic `Evidence` renderer performs no unit normalization, period alignment, cell comparison or calculation. | The instruction promises a period/unit/value check, but the interaction is a text checklist. It does not show why financial-data extraction is useful. |
| Autentic / `p_1b6f5ea8f77f3c28` | Choose audience/focus/theme → authored excerpt and design idea | `autentic.json` starts at `inspection`. All later dependencies reference `input`; none reference audience `setup`. | Changing audience does not change the later interview material. Picking a theme swaps text rather than letting a user inspect and synthesize evidence. |
| Abridge / `1056` | Select fictional transcript facts → editable note fields with source indices | `Evidence` adds/removes the selected field and keeps edits per locale. | Already a useful bounded activity. Leave its workflow in place; source indices should be understood as provenance, not verification of arbitrary edits. |
| Granter / `p_35d86b7001bf3f1b` | No prepared example | Public prepared GET says `not_generated`. | Do not fabricate a reviewed interaction or consume generation credits for this audit. |

Code evidence: `frontend-next/src/components/demo/reviewed/record-tasks.tsx`, `reviewed/catalog/records.ts`, `experience-player.tsx`, and `backend/data/demo_profiles/autentic.json`.

## Selected task contracts

### Exa — build a small evidence set

1. **Task:** find passages relevant to a research question and retain the useful evidence.
2. **Input:** editable keywords in Chinese or English and an explicit small fictional collection.
3. **First result:** a relevant source title and inspectable passage immediately; changing the query changes the matched set. A user can add/remove passages from a research excerpt list.
4. **Evidence:** deterministic local matching over authored documents. Empty results stay empty; no web retrieval, synthesis or vendor execution is implied.
5. **Next action:** inspect another source, refine the query, retain passages or visit official Exa.

### Daloopa — reconcile source figures with model cells

1. **Task:** bring a fictional filing's figures into a model and spot a period/unit/value mismatch.
2. **Input:** a selected reporting unit and editable model cells for named periods and metrics.
3. **First result:** a compact period-by-metric table with source values and an intentional value mismatch. A source reference opens the supporting excerpt; copying a sourced value resolves the mismatch. Derived growth uses the visible entered values only.
4. **Evidence:** local arithmetic on fictional figures, not investment advice, real company data or Daloopa extraction. Edited cells remain visibly distinct from source matches.
5. **Next action:** reconcile another cell, compare periods, inspect the original passage or visit official Daloopa.

### Autentic — trace a research theme to selected answers

1. **Task:** turn selected interview passages into a reviewable theme and a next research question.
2. **Input:** audience selection, authored interview passages and an editable synthesis.
3. **First result:** audience-specific fictional answers with one selected passage and its suggested theme. Switching audience changes the material; adding/removing evidence changes the evidence set without overwriting user edits.
4. **Evidence:** fictional interview excerpts and locally authored theme suggestions, not real interviews, findings or model inference. An edited synthesis must retain source passages for review.
5. **Next action:** check another passage, revise the theme or follow the official trial route.

## Required checks

- Exa: natural Chinese and English phrases, source-level matching, unsupported queries, empty query, excerpt collection and removal.
- Daloopa: both reporting units, period alignment, decimal handling, invalid input, source reconciliation and derived arithmetic from visible values.
- Autentic: audience-specific material, source selection, edited text persistence, independent edits per audience and locale, no stale sources after switching.
- All: keyboard controls, clear form labels, no decorative generic icons, no POST/network execution from the activity, honest source/example labels, and preserved shared logos. Browser validation remains a separately reported requirement; logic tests do not establish visual quality or human understanding.
