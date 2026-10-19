# Product detail refresh — 2026-10-19

## Experience contract

1. A visitor opens a software or hardware product to understand its purpose, see why it merits attention, and decide whether to visit the official product or continue exploring.
2. Public product records supply the description, research note, source, funding and dates. If a prepared independent example exists, its original product-specific preset supplies the input; page arrival only reads that example.
3. The first visible useful content is the product description with website/favorite actions and the research note. Once a prepared example loads, its selected input and output appear without another launch step. Missing examples use a compact optional entry, not a blank financial grid.
4. Product records are attributed public information, not live measurements. Example output remains explicitly independent and illustrative, not vendor execution. No product photos, claims or fields are fabricated. Missing financing and valuation are omitted rather than rendered as zero or a large dash.
5. Visitors can change prepared presets, inspect sources, favorite, visit the official website, or continue to related products. Starting a new example requires an explicit generate click; ordinary arrival, deep links, language changes and read-only retries do not generate.

## Representative checks

- Healthleap: source-backed description and research note, funding present, valuation absent; independent clinical excerpt remains labeled as fictional and not vendor output.
- pib.rocks: source-backed open-source hardware description; no financing or valuation slots when unavailable. Its example is conceptual, not device operation or measured hardware performance.
- Unverified identity: prominent verification note; official CTA becomes a website search and automatic examples are withheld.
- Ready, absent, preparing and failed example reads: keep the product itself readable; explicit retry reads only. Existing generation/recovery behavior remains behind a deliberate generate click.
- Chinese and English, desktop and narrow layouts, visible keyboard focus, favorite synchronization, source links and `?demo=1#try-demo` anchor.

## Evidence boundary

Agent reviews, code checks and browser screenshots establish implementation behavior and layout only. First-time visitor comprehension still requires a human check; no human comprehension outcome is claimed here.

## Verification results

- All 128 frontend tests passed across 17 files, including detail rendering, unverified identity gating and read-only prepared-example requests.
- Targeted ESLint and the production build (including TypeScript) passed.
- Local browser checks used real API data: Healthleap's prepared example displayed automatically; changing the risk preset changed the input and output. Favorites survived reload and could be removed; Chinese/English content changed immediately.
- Desktop, 390px mobile and 320px narrow layouts were checked, including dark/light themes; the measured document width did not exceed the viewport. The hardware detail showed a compact optional example entry and omitted absent funding/valuation.
- Three independent agents reviewed content/evidence, visual hierarchy and interaction/accessibility. Final reviews found no blocking issues after the suggested layout and focus changes.
- Screenshots are retained outside the repository in the task's visualization folder. Production verification is performed after the commit is deployed.
