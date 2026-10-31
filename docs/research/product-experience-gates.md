# Product experience gates

Updated 2026-10-12. Applies to every DarkHorseRadar example, existing and future, including the legacy examples route. Passing structural tests does not establish that visitors understand the product. See [demo-focus-coverage.md](demo-focus-coverage.md) for implementation coverage and verification limits.

## Current task contract

1. The visitor arrives to decide whether an AI product is useful by inspecting a representative input and output.
2. The page supplies a prepared input and preset; choosing another preset displays its prepared example rather than running the vendor service.
3. The first useful result is visible on opening: for example, a fictional research excerpt with a theme, a creative brief with a proposed sequence, or a specification comparison.
4. The result is an independent illustration; public source links support product descriptions, not the authenticity of fictional quotes, findings, media, or measured results.
5. The next useful action is to compare another relevant example or visit the official product; real execution, output quality, and first-time visitor comprehension remain to be verified.

Before adding a product, make these five sentences concrete for its task, input, first visible artifact, evidence status, and next action. Share standards, not a mandatory sequence or one identical artifact for every product.

## Review gates before promotion

- **Entry and first value:** show one useful artifact immediately, with a concise explanation of the product's job. A default preset is an example being inspected, never a completed user task.
- **Focus:** use one centered content area. Keep narration, sources, longer explanations, and secondary tools available on demand. Do not require setup, a review checkbox, or a completion screen to inspect the example.
- **Choice:** offer only changes that affect relevant visible content. Resolve dependent presets safely, reset affected branches, preserve independent edits, and keep every section reachable by its name.
- **Product fit:** use a natural artifact: excerpt and theme, proposed sequence, comparison, list, source-backed specification, or local sample app. A storyboard is a plan; do not fabricate a cup image, video playback, completed interview, or vendor output to make it look more tangible.
- **Evidence:** retain a short independent/example label beside the artifact. Keep source links available. Vendor claims, fictional passages, recorded presets, local arithmetic, and real execution are different evidence states; labels must match the actual renderer behavior.
- **Recovery:** check keyboard controls, narrow viewports, returning to the catalog, preset reset, external links, errors, and downloaded examples. Downloads must identify the prepared path and unchanged presets rather than claim completed work.
- **Human check:** ask a first-time tester what the product does, what just happened, and what they would do next. Record their actual answer and hesitation. Agent critique, screenshot review, and automated tests do not pass this gate.

## Product-specific applications

| Product or category | First useful artifact | Required distinction |
| --- | --- | --- |
| Autentic | Fictional interview passage with a related theme and highlighted supporting phrase | No interview occurred; the passage is not vendor output. Offer the official trial and its contact-detail requirement. |
| Higgsfield / creative tools | Brief and proposed shot sequence | A text concept does not establish generated imagery, rendered video, or model quality. |
| App builders | Working local sample app | Local interactions demonstrate the idea; the sample was not generated or deployed by the vendor. |
| Search, analysis, operations | Prepared result, comparison, or list appropriate to the task | A preset is not a real search, verified finding, submitted action, or connected account. |
| Hardware / infrastructure | Concept comparison or explicitly illustrative arithmetic | No device operation or measured performance is demonstrated. |
| TCGlens, when reviewed separately | Original listings with visible version attributes and separate price components | Asking prices do not establish identity, authenticity, condition, final checkout cost, or lowest price. This is not a claim of current DarkHorseRadar demo coverage. |

## What is enforced

The v2 contract accepts **1–6 example sections**; its generation prompt prefers **1–3** and requests a product-specific input/output relationship. A generation-only guard requires an artifact on **every option in the first section**. Existing cache replay does not acquire this new generation requirement.

Bounded bilingual artifact fields allow excerpt, sequence, comparison, list, and text. Validation checks supported fields, safe cited sources, valid dependencies, and literal highlight substrings, and rejects known markup, media/URL, measurement, and execution claims. These checks do not establish factual truth or semantic fit.

Old v2 caches remain readable through a complete-text fallback that preserves the selected label and output. It neither truncates meaning nor invents new media or evidence. Legacy v1 examples use their own schema and focused renderer. Prompt changes do not regenerate or semantically repair either collection.

## Homepage category discovery — 2026-10-31

- Task: scan emerging AI products or narrow the catalog by category in Chinese or English.
- Input: a product search, category choice, or hardware/software filter.
- First visible result: compact search and recent product rows; categories open on demand in a searchable text-only menu.
- Evidence: existing sourced product records and SmartLogo assets; design mock descriptions and logos are never production data.
- Next action: inspect a product, read its source, save it, or visit its official website.
- Validation: shared layout for both locales, responsive menu, keyboard dismissal and selection, search and empty state. Browser checks and automated checks do not establish first-time user understanding.
