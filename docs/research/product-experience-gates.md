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

## Homepage featured products — 2026-11-05

A PM opens the homepage or filters the featured products to find one product worth investigating. The first card should show the real product identity, what it does, and a visible route to its details on a 390 × 844 phone. The catalog supplies the description, score, and editorial rationale. Keep the supporting source directly accessible and the longer rationale available on demand. A visitor can open Details, save the product, follow its source, or continue to the available demo or website.

Browser checks against the live catalog showed the English lead card at 317 px tall on a 390 × 844 viewport, down from 500 px for the same product. Details ended at y=643, above the navigation at y=784. The Chinese dark-theme check, keyboard disclosure, saved-state persistence, category filter, search and detail navigation also passed. These checks measure layout and behavior; first-time visitor comprehension still needs a human session.

## Catalog, reading and saved views — 2026-11-05

Visitors search or filter real catalog records, compare products across rows, and open a detail, source or saved item. Each catalog row should immediately show identity, purpose and actions in a consistent order. The recorded date stays with the identity. Notes expose the rationale, demo and website. News keeps its attribution and evidence label. Demo surfaces keep the independent-example and credit information beside the choice it affects. Navigation, keyboard input and reduced motion must work across both languages.

Figma Make and browser screenshots informed the masthead, aligned catalog rows, dated news feed, demo gallery, saved drawer and support pages. Browser checks at 320, 390, 768, 1024 and 1440 pixels measured matching identity, description and action positions across featured products, the library and search. The first saved entry followed the filters by 12 pixels in each case. Keyboard disclosure and drawer focus, saved-state persistence, search, sources, swipe and reduced-motion behavior passed. Prepared demos opened without a generation request. The desktop English and phone Chinese screenshot sets cover 16 page and interaction states. First-time visitor comprehension still requires a human session.

## First visit from discovery to a prepared example — 2026-11-05

A new visitor needs an unfamiliar AI product to start with, a plain-language account of what it does, and a route to evidence or an example. The hero uses a real catalog record. In a prepared example, the visitor changes one provided input and reads the corresponding authored result. The selected control stays in place; any change cue is brief and optional. Keep vendor provenance, example disclosures, and generation costs visible where the choice is made. Compare desktop and phone behavior using the same record, and test reduced motion and keyboard interaction.

The [Make prototype](https://www.figma.com/make/plrCC8NvzPeh75LuZOPjqe/Build-Darkhorse-Radar-Homepage) compared 320 ms and 560 ms hero treatments. The native Figma Motion studies isolate the [460 ms radar sweep](https://www.figma.com/design/CwfXemf7jlH7zWiqIsjRCz/?node-id=2-27&timeline=keyframe) and the [180 ms result reveal](https://www.figma.com/design/CwfXemf7jlH7zWiqIsjRCz/?node-id=2-36&timeline=keyframe). The site uses the single sweep and the result reveal. The real chip-materials presets update both requirements and direction. Only the direction animates.

Browser checks at 320, 390, 768 and 1280 pixels covered both locales, keyboard choice and focus, step changes, preserved presets, the direct hero links, filters, horizontal overflow and reduced motion. A missing prepared example left the product link usable. Viewing and switching examples issued no generation request. These checks verify the interactions. Understanding by first-time visitors still needs observation with people.

In the working checklist example, the visitor adds a task and checks it off. The first result is the checked item and updated completion count. Changing the prepared guidance keeps that local task available until reset. The product example remains explicitly independent.

## Inspecting artifacts across products — 2026-11-06

A developer chooses a project brief, inspects the responsibilities of each authored workspace and reads an annotated code sample. A video planner selects a prepared shot and inspects its direction. A product evaluator compares the inputs and outcomes of two eligible presets, including older text-only records. Each opens with its actual authored content. Examples illustrate a task and never execute a snippet, generate footage, or claim vendor results. After inspection the visitor can choose a different branch or follow the source. Test all three tasks, both player entry paths, a legacy record, and keyboard and narrow-screen access.

Snapshot verification covered 169 publicly ready products and all 1,077 options in Chinese and English. The older multi-part, text-only format qualified 72 products for a user-assembled plan. This allows visitors to retain chosen configurations and download them with their sources, without treating preset defaults as work the visitor completed. Existing saved content is preserved. New list and sequence generations require inspectable entries. Browser checks exercise collection, reordering, plan downloads, clipboard, comparison, return to a previously edited preset, and the difference between a read-only visit and the explicit generation action. Human comprehension and real vendor output quality require separate evaluation.

## November 6 review of the 72 text-only examples

For each of the 72 prepared records, compare its old four choices against the product source and identify a concrete visitor task. Record the individual input, operation and visible result in the [individual audit](legacy-demo-audit-2026-11-06.md). Give the visitor a fictional, inspectable starting artifact and an action that changes it locally. Separate research concepts and device schematics from usable vendor software. Keep the source and next step reachable, preserve read-only entry and check each route with a browser. Human comprehension requires separate observation.
