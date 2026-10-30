# UI copy audit — 2026-10-29

## Task contract

- Task: find a relevant AI product, inspect its description or prepared example, and save it or visit its official site.
- Input: a product query, category/type filter, product selection, or prepared example option.
- First visible result: product records on catalog surfaces; the selected input/output artifact inside a demo.
- Evidence: descriptions retain sources and discovery dates. Examples remain explicitly independent, fictional or local samples; removing repeated instructions does not turn them into vendor output.
- Next action: filter, open details, compare a preset, save, or follow the official product link.

## Audit decisions

| Surface | Decision |
| --- | --- |
| Navigation and home, both languages | Remove repeated brand captions, decorative headings, section narration and shortcut subtitles. Let search, categories and links express the available actions. |
| Discover | Keep named Skip/Save controls and one first-visit gesture guide; remove repeated introductory instructions and default gesture narration. |
| Search | Keep heading, query label, filters, result count and recovery states; remove pre-search narration. |
| News | Keep actual sources, dates and filters; remove editorial kicker, repeated filter summaries and summaries identical to the headline. |
| Product cards and details | Keep actual descriptions, differentiators, score labels, dates and sources; remove repeated “product highlight” prefixes and related-product narration. |
| Demo catalog and players | Consolidate provenance labels and quota help; retain a visible evidence label next to each artifact and a clear generation cost on its action. |
| Assistant and favorites | Remove the assistant's welcome narration and provider tagline; show each favorite's tier once. Retain query labels, suggested questions, favorite counts and empty-state recovery. |
| Privacy, support, sources, corrections | Keep substantive help and policy content: explaining these topics is the page's task. |
| Legacy Express frontend and unused components | Inspected for scope; not active product surfaces, no redesign. |

## Verification

- Final checks: 128 tests in 17 Vitest files passed; ESLint passed; Next.js production build (webpack) and TypeScript passed; `git diff --check` passed.
- Local browser, real production API reads: Chinese and English home; home search for Dream returned six results; product detail opened; switching the prepared preset updated its input and output while retaining the fictional-example label; favorite/save/remove and the panel worked; demo ready filter and expandable quota help worked; Discover skip advanced the card and counter; news market selection returned the China feed; assistant opened with labeled input and suggestions.
- Responsive review: 390 × 844 browser override on home, demo catalog and product detail; measured page width and scroll width were both 375 CSS px (no horizontal overflow). Desktop layouts were also visually reviewed. Browser error-log query returned no errors. Override reset afterward.
- Only prepared examples were inspected. No vendor execution, paid generation, model-quality test, or first-time human comprehension test was performed.
- Integration uses the latest remote `main`, preserving its newer product-detail implementation. Existing unrelated changes in the original checkout are excluded.

Automated checks and agent visual inspection do not establish first-time user comprehension.
