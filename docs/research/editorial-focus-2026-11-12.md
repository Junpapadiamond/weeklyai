# Product-first editorial focus — 2026-11-12

## Task contract

1. A PM opens a product card or detail page to decide whether its capabilities are relevant to a task.
2. The input is the existing bilingual product record, its cited article evidence, and the selected UI language.
3. The first visible result explains the product's job; the rationale adds a concrete difference, use case or reported result instead of repeating its funding news.
4. These are editorial summaries of attributed sources, not product tests. Company-reported results remain attributed; a clinical study, prototype or announced capability is not proof of effectiveness.
5. The visitor can inspect the source or official product, save it, or open an independent prepared example. The change does not turn an example into vendor output or trigger generation.

## Scope and field responsibilities

- Keep useful Chinese translations in `frontend-next/src/lib/product-utils.ts`; rewrite the financing-led rationale overrides without changing localization precedence.
- In `discovery-deck.tsx`, an absent rationale no longer promotes the financing amount into the product highlight. The financing data remains available in its dedicated context.
- Backfill `description`, `description_en`, `why_matters` and `why_matters_en` only where listed below. Update every matching featured/weekly/rising-star record in `crawler/data` and `backend/data` together so the repository's richer-text merge cannot restore an older paragraph.
- Keep scores, criteria, discovery/news dates, source URLs and evidence quotes, logos, financing fields, and latest-news fields unchanged. This is a copy correction, not a historical rescore or a new discovery.
- Financing can remain useful context, especially for capital efficiency or a funding event. Do not remove keywords mechanically or replace missing evidence with invented product outcomes.

## Backfill evidence and intended result

| Product | Existing source / evidence | Edit |
| --- | --- | --- |
| Synapse Analytics | [Source article](https://launchbaseafrica.com/2026/11/03/south-africa-and-egypt-contest-africas-ai-funding-crown); stored quote explicitly says the company reports supporting over $200m of lending and reducing clients' non-performing loans by up to 40%. | Description states the banking decisioning task; rationale attributes those reported results instead of treating VC recognition as product validation. |
| Primero | [Source article](https://latinamericareports.com/15-ai-leaders-to-watch-in-2027/15575); stored quote identifies legacy-system integration and names Kimberly-Clark de México and SmartFit as customers. | Separate capability from customer evidence; remove financing repetition and the inference that planned offices prove expansion capability. |
| Daytona | [Source article](https://tech.eu/2026/10/20/daytona-hits-1b-valuation-with-60m-series-b-for-ai-agent-cloud/); existing description explains isolated agent environments; stored quote attributes 25-fold growth in revenue run rate to the company. | Keep the execution environment description; rationale connects it to agent tasks and attributes the growth, omitting valuation and investor lists. |
| Rently | [Source article](https://fintechnews.sg/139924/proptech/proptech-startups-from-singapore-to-watch); stored quote records S$36.3m of rental transactions in the first nine months of 2026, 2.5 times the corresponding 2025 period. | Keep the rental-payment use case and transaction evidence; remove the duplicated debt-financing tail from the rationale. |
| AI Diagnostics | [Source article](https://launchbaseafrica.com/2026/10/12/african-healthtech-2026); stored quote records over 1,000 screenings in South Africa and research in over ten countries. | Emphasize screening/research activity, without presenting participation counts as clinical-effectiveness validation. |
| Holo | [Source article](https://www.eu-startups.com/2026/10/vilnius-based-holo-raises-e5-million-to-put-marketing-on-autopilot-for-small-businesses); company-reported ARR, paid businesses and less than €1m raised before the round. | Retain useful capital-efficiency context, correct the Chinese mistranslation of money raised as operating cost, and attribute reported figures. |
| Harvey | [Existing source](https://techcrunch.com/2026/01/19/here-are-the-49-us-ai-startups-that-have-raised-100m-or-more-in-2025/) and stored description identify legal-document analysis and contract review. | Explain the legal workflow; do not infer adoption from the size of a financing round. |

## Chinese overrides

The targeted overrides are Kontext, Outerlimit, Sakana AI, SkildAI, Frankenburg Technologies, AI2 Robotics, Vertical Compute, Abridge, Anysphere (Cursor), Google x Gentle Monster Android XR Glasses, Google x Warby Parker Android XR Glasses, Harvey, Hippocratic AI, RobCo Modular AI Robots, SandboxAQ, KEWAZO, Ivee, Godot, NeuReality, SEEQC, Basis, Xross Road, Modveon, Shizuku AI, Helpfeel, Upscale AI, Snorkel AI, ValkaAI, Foodforecast and LMArena. Unrelated translations remain intact.

Most edits shorten existing product facts in the corresponding featured record or the existing curated translation. They are not a fresh fact check of every historical record. For the following thin descriptions, official product pages were read on 2026-11-12 before editing:

- [Frankenburg Technologies](https://frankenburg.tech/): describes guided interceptor systems and a manufacturing focus. The copy only identifies the product category and announced focus, not a new AI-performance claim.
- [Upscale launch announcement](https://upscale.com/blogs/upscale-ai-launches-with-over-100-million-seed-round-to-democratize-ai-network-infrastructure-and-advance-open-standards): describes AI network infrastructure and open standards including SONiC, UAL and Ultra Ethernet. The copy describes the planned architecture, without claiming measured speed or savings.
- [Hippocratic AI](https://hippocraticai.com/): lists appointment scheduling, patient intake and follow-up; explicitly states its agents do not diagnose or prescribe. The scope limitation stays in the copy.
- [KEWAZO](https://www.kewazo.com/): identifies LIFTBOT material lifting and ONSITE operational-data analytics. No vendor savings numbers are added.

## Exact changed data scope

Seven products, 25 stored record copies and nine files: the crawler/backend featured files; `dark_horses/week_2026_42.json`, `week_2026_43.json` and `week_2026_46.json` in both data roots; and `crawler/data/rising_stars/global_2026_42.json`. The backend tree has no counterpart for that rising-star file. Synapse Analytics, Primero, Daytona, Rently and Holo each have four changed copies; AI Diagnostics has three and Harvey has two. Only the four description/rationale text fields change.

The frontend changes comprise 30 existing Chinese rationale overrides, four existing Chinese description overrides, the discovery-card financing fallback and one existing test expectation that previously required a financing amount in Sakana AI's rationale.

## Verification

- Existing `product-utils.test.ts`: 26 tests passed.
- ESLint for `product-utils.ts` and `discovery-deck.tsx`: passed.
- Parsed changed JSON and compared each record against `HEAD`: all 25 changed records are one of the seven named products; array lengths, record identity and every field outside the four allowed text fields are unchanged. Edited copies agree across files.
- Browser validation must inspect Chinese and English detail/card copy with real records after integration. Automated checks and agent review do not establish first-time visitor understanding; no human comprehension session has been run.
