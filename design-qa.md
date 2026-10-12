# Demo focus design QA

Updated 2026-10-12 14:11 EDT. Scope: the selected third concept, adapted to every existing demo renderer and product-specific content.

## Visual truth and comparison

- Source: `C:/Users/徐晨濬/.codex/generated_images/01a130f4-ebd6-7ee0-b614-51c3c3503fb4/exec-84576e5b-c704-4067-a5da-b82f26d0acd6.png` (1487 × 1058).
- Production: `https://darkhorseradar.com/product/p_1b6f5ea8f77f3c28?demo=1#try-demo`.
- Evidence directory: `C:/Users/徐晨濬/projects/reddit-cold-start-2026-10-12/`.
- Full-view comparison: source and `demo-focus-production.jpg` were opened together in one tool result. Desktop CSS viewport 1487 × 1058, English, light theme, usage-barriers / location-privacy example. Source is 1487 × 1058 px; browser output is 1472 × 1047 px (about 0.99 capture scale). Compare equal-width content regions rather than the global navigation or pixel-level antialiasing. No image pixels were edited.
- The full-resolution comparison makes the question, highlighted phrase, related theme, and buttons readable; no separate magnified crop is necessary. The mock's fictional words differ intentionally from the curated example, while the evidence status and interaction are the same.
- Final focused comparison: `demo-focus-final.png` is a direct Chrome capture of the entire 1040 × 991 CSS-pixel example panel at 1:1 scale, including the logo, short boundary, excerpt, controls, disclosures, and vendor handoff. It was opened together with the source as the final comparison input. This excludes the host site's navigation and surrounding product description; both retain the same single-column composition. No remaining actionable P0/P1/P2 findings.
- Additional captures: `demo-focus-desktop-local.jpg`, `demo-focus-mobile-local.jpg`, `demo-focus-legacy-local.jpg`, `demo-focus-production-dark.jpg`. Local narrow viewport was 355 CSS px at the user's existing zoom; production narrow viewport is 390 × 844.

## Findings and iteration history

1. **P1, resolved:** the old page required reading multiple explanatory panels before seeing value. The shared player now opens a prepared artifact immediately; both catalogs hide while playing. Long narration and provenance remain in details controls.
2. **P2, resolved:** early artifact styling split the input and result into unrelated green/yellow panels. It now uses one restrained surface with matching rose emphasis and a directional icon. The secondary section picker moved below the first result.
3. **P2, resolved:** changing the native section select stole keyboard focus. It now retains focus; two consecutive ArrowUp operations were verified. App guidance choices remain reachable, and downloaded examples retain the complete explanatory qualifications and takeaway.
4. **P2, resolved:** the excerpt initially lacked a concrete research context. The final production response and mobile screenshot now show the workout-buddy label directly above the fictional exchange.
5. **P2, resolved:** the transparent black vendor logo was hard to read on the dark surface. The updated production dark screenshot shows the original logo legibly on its white surface; computed background is rgb(255, 255, 255).

## Required fidelity surfaces

- **Typography:** existing site font and real brand names remain. One prominent task heading, readable question/answer, small provenance text, and a clearly distinguished theme replace the old three-column hierarchy. Long legacy content is not arbitrarily truncated.
- **Spacing and layout:** one centered artifact and one group of relevant choices. Existing global navigation and the close control are retained because this is an integrated product page. Section navigation uses a native selector so different products can have different section counts. These are intentional adaptations to the all-demo scope, not a pixel clone of an interview-only page.
- **Colors:** existing warm/light and dark tokens; restrained rose is shared by the supporting text and theme. Keyboard focus is visible. No decorative gradients or fake media surfaces.
- **Assets:** original SmartLogo sources remain. Phosphor icons are used for arrows and controls. The generic cup/video workspace was removed from active rendering; structured text sequences do not claim to be rendered video. The directional icon is an intentional accessible substitute for a responsive curved annotation, not a replacement product image.
- **Copy:** the job, next choice, and local example label stay visible. Longer limitations and sources are available on demand. The vendor handoff remains explicit. Future generation requires concrete opening artifacts rather than explanatory steps alone.

## Functional evidence and limits

- 183 Python tests, 117 frontend tests, full ESLint, and the production build/TypeScript passed. The final scenario-label edit also passed its 97 relevant backend tests.
- Local browser: Autentic branch changes and export contents; Higgsfield sequence changes; Lovable add/check/delete and alternative guidance; legacy Exa prepared query and named sections. All used prepared content or local interaction.
- Production browser: Autentic opens the result immediately; changing the theme changes both excerpt and highlight. Helix's old cache uses the full-text fallback. The catalog disappears while playing, restores search focus on return, and retained quota 2/3 before and after replay. Production console error check returned no errors.
- English/Chinese and narrow layout were inspected. No horizontal overflow was observed at 355 local / 390 production CSS px. Existing sticky mobile navigation means the full example can require ordinary vertical scrolling.
- Tractable and XCENA were not ready against the local catalog; their stored specs passed compatibility checks, not live browser playback. No paid generation, vendor service execution, or new first-time human comprehension result was claimed.
- Local download event waiting timed out in the browser tool, but the resulting file was independently found and read in Downloads. Local production-preview startup was rejected by automatic approval without a detailed reason; verification continued on the authorized deployment.

## Final verification and follow-up

- Application commit `823c1d426c1d1019c000960ba927b4da54428340` is READY in both Vercel projects. Final browser evidence includes the scene label, correct selection/highlight, and dark logo treatment. The production console check returned no errors.
- The final narrow production capture is `demo-focus-production-mobile.jpg`; result and comparison controls fit its content width, with ordinary vertical scrolling. Temporary viewport overrides were reset after capture.
- P3 follow-up: review older cached wording product by product, and test comprehension with a real first-time visitor. Automated compatibility does not establish semantic quality or human understanding.

final result: passed
