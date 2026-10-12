# Demo focus coverage

Implementation inventory, 2026-10-12. This records local code and committed data, not the number of available demos in production. No deployment is verified by this document.

## Routes and renderers

| Surface | Rendering path | Presentation coverage |
| --- | --- | --- |
| `/demo`, including `?filter=ready` | `demo/page.tsx` → `DemoGallery` → `ProductLiveDemo` → `ExperiencePlayer` | One prepared artifact is visible on opening; other presets and sections remain accessible. |
| `/product/[id]`, including `?demo=1#try-demo` | Product page → `ProductLiveDemo` → `ExperiencePlayer` | Same v2 presentation with the product-detail entry. |
| `/demo/examples` | `demo/examples/page.tsx` → `DemoExplorer` → `DemoPlayer` → `DemoWidget` | Separate legacy renderer; direct named sections, initial widget content visible, catalog hidden during playback. |
| `/demo-feedback` | Feedback information page | Existing reporting destination; not an interactive renderer or proof of a response-time commitment. |

Component paths are under `frontend-next/src/components/demo/`; route paths are under `frontend-next/src/app/`. `ProductDemoSection` has no current call sites. The former `ExperienceWorkspace` is no longer used by `ExperiencePlayer`.

## Local data and delivery

| Source | Inventory | Serving rule |
| --- | --- | --- |
| `backend/data/demos/*.json` | **63 v2 envelopes / 56 distinct product names:** 7 curated and 56 pregenerated envelopes; multiple fingerprints can exist for one product | Matching bundled cache follows curated-profile lookup and precedes the durable runtime cache. |
| `backend/data/demo_profiles/*.json` | **2 domain profiles:** Autentic and Higgsfield | Curated domain profiles override cached versions. |
| `backend/data/demos/published/*.json` | **5 legacy seeds:** Apptronik, Daloopa, Exa, Fireworks AI, Rogo | Separate v1 repository: process cache, Mongo `demos`, then JSON fallback. |
| Runtime caches | Not inventoried in this pass | v2 uses Mongo `demo_cache`, with SQLite for local development; deployed contents and configuration can differ. |

The 63 envelopes and 5 legacy seeds have matching copies in `crawler/data/demos/`; these are mirrors, not additional products. Counts are not additive unique-product totals. Reachability also depends on current catalog fingerprints and runtime state.

Main service: `backend/app/routes/demos.py`, `demo_experiences.py`, `demo_contract.py`, `demo_store.py`, and `demo_profiles.py` under `backend/app/services/`. Legacy service: `backend/app/routes/legacy_demos.py` with `demo_service.py`, `demo_spec.py`, and `demo_repository.py`. Routes, source data, caches, and generation cost controls remain separate from presentation changes.

## Artifact and compatibility coverage

- **Research:** Autentic opens a fictional excerpt/theme artifact with literal supporting-text emphasis. This is not a completed interview or a claim of synthesis accuracy.
- **Creative work:** Higgsfield uses a brief and proposed text sequence. No substitute cup graphic, simulated media playback, or generated-video claim is needed.
- **Other v2 products:** bounded `excerpt`, `sequence`, `comparison`, `list`, and `text` artifacts; local app previews for app builders; explicitly illustrative arithmetic for dial controls. No generic four-step journey is required.
- **Existing v2 caches:** `demo-presentation.ts` resolves a prepared path and preserves the full selected label/output when structured artifacts are absent. This improves access, not the factual quality or reading load of every old record. Replay does not regenerate or rewrite stored examples.
- **Future v2 generation:** 1–6 sections, prompt preference for 1–3, and a concrete artifact required on every first-section option. Common validation keeps artifacts optional for old caches. Invalid new output uses the existing bounded repair/failure path rather than fabricating a fallback.
- **Legacy v1:** all eight supported widgets remain reachable: query response, split comparison, pipeline, specification matrix, scenario branch, screenshot hotspot, parameter dial, transcript. A query always displays the first prepared response initially, even when stored `mode` is `live`; the renderer does not call the vendor. Sliders identify their actual local behavior. Legacy generation retains its separate schema.

Preset selections are not completion records. Explanations and provenance are collapsed, while local example labels remain visible beside artifacts. Source links and optional tools remain available. This scope does not certify old copy as evidence or independently verify vendor claims.

## Verification snapshot and limits

- **183 Python tests and all 117 frontend tests passed.** Full ESLint and the Next production build (including TypeScript) passed, including the final gallery focus change. The later scenario-label edit passed 97 relevant backend tests.
- Local Chrome checks: Autentic switches excerpt/theme and dependency branches; a native select retains keyboard focus; the downloaded file includes explanatory limits and the complete takeaway. Chinese narrow-screen layout has no horizontal overflow. Higgsfield switches proposed shot sequences. Lovable supports add/check/delete and both guidance choices. Legacy Exa opens prepared output with its catalog hidden.
- Tractable and XCENA returned the existing not-ready state against the local catalog. Their old stored specs are covered by compatibility tests, not a claim of completed browser playback. Generation was disabled during local checks.
- Production application commit `823c1d426c1d1019c000960ba927b4da54428340` was READY on frontend and backend, then verified in Chrome: Autentic, a Helix cache from the current production catalog, catalog focus restoration, and unchanged replay quota. See project-root `design-qa.md` for captures and limits. No paid generation, real vendor execution, or first-time human comprehension test is established here. Agent review remains simulated expert judgment.
