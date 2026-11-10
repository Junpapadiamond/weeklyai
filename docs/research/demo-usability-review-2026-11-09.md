# Demo usability review — 2026-11-09

## Task contract

- Task: understand what a product does by trying one relevant example, then decide whether to visit its official product.
- Input: concrete sample requests for Clutch, existing product-specific controls elsewhere, and an optional language change.
- First visible result: a readable example result, including every relevant result item without opening each one separately.
- Evidence: independent fictional examples and local deterministic rules; no vendor execution, security assessment, or measured vendor performance.
- Next action: change a meaningful input and inspect its consequence, or visit the linked official product. Notes and rearranging content are optional tools.

## Current-run observations

Three independent agents reviewed content, interaction, and the discovery/detail journey. The primary reviewer also reproduced the supplied Clutch screenshot on the live product page.

1. Clutch's code-analysis preset prohibited all environment variables and deployment configuration; this confused sensitive credential values with ordinary configuration and authorized service access.
2. Switching to the code-analysis role still produced a customer-service ticket in the later log section. The apparent flow had no consistent task context.
3. The generic item renderer hid even a two-item result behind selection controls. Its prominent interactions saved excerpts instead of demonstrating the product's work.
4. Abridge's local evidence activity lost selected passages and text edits when changing language because the activity key included the locale.

## Implementation scope

Clutch receives a product-specific local access example and corrected shipped fallback data. Generic lists display full results with optional tools. Language changes preserve activity state; unedited example text follows the selected language, while user edits remain available in the language in which they were entered. A reset intentionally clears those edits.

## Verification boundary

Agent walkthroughs, screenshots, automated tests, and source review are not first-time human comprehension testing. This change does not claim that all catalog examples are semantically reviewed or that Clutch's real system was tested.

## Completed verification

- Frontend: ESLint, TypeScript, production build, 138 Vitest checks, and 2,362 catalog records passed.
- Backend: 488 tests plus 11 subtests passed; the Clutch checks confirm the shipped corrected cache wins over an equivalent stale Mongo entry without generation.
- Clutch browser flow: both tasks; request switching; simulated grant and revocation; denial despite a grant for production, plaintext credentials and unrelated records; language state preservation; keyboard controls; narrow layout.
- Higgsfield browser flow: all three shots visible together; optional reorder controls; focus retention after moving; exported order, example disclosure and source retained; narrow layout.
- Abridge browser flow: select a second source, edit the Chinese note, switch to English and back. Both sources stay selected and the edited Chinese note returns; unedited English defaults remain English.
- Screenshots and the inspected export are stored in the current chat's `demo-audit` visualization folder. These are current-run evidence, not a vendor benchmark.
