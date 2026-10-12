# Demo generation reliability

Updated 2026-10-12, America/New_York.

## Visitor contract

The visitor chooses a product from the home page and opens its example. A prepared example should be immediately inspectable without a model request or personal generation charge. A missing example can be generated from the catalog's public product information, then validated and saved for reuse. The output remains an unofficial illustration, not vendor execution. If the connection is interrupted, checking for a result must not purchase another generation.

## Observed failures

- At 14:16:59 EDT, Kello failed text validation after 29.022 seconds; its repair timed out at 52.095 seconds total. InteNext recorded the corresponding two non-streaming `claude-sonnet-5` completions at approximately 29 and 30 seconds. The previous 55-second total budget left insufficient time for the repair.
- Finches hit the previous 35-second read timeout, followed by another timeout at 52.169 seconds total. A relay may continue and charge for a completion after the client stops waiting.
- Both products already had valid pregenerated examples. Their raw catalog records omitted `is_hardware`, while the public API normalizes it to `false`. This was the only fingerprint-field difference, so the prepared endpoint incorrectly returned `not_generated`.
- Production had 38 ready examples before this fix. A local catalog is not identical to production, so its counts are not a production success metric.

## Changes

- Preserve all existing fingerprints; read both equivalent `is_hardware: null/missing` and `false` keys. Apply the same lookup to the catalog, prepared playback and generation cache check. Actual changes in product facts and `is_hardware: true` still invalidate the cache.
- Allow 90 seconds for generation/one repair, with a 110-second proxy timeout, a 115-second browser POST timeout and a bounded 130-second generation/poll window. Vercel functions remain limited to 120 seconds per request. No new provider, credential or spending limit is configured.
- Do not automatically retry a provider read timeout, including a timeout wrapped during body iteration. Connection setup failures and eligible server failures can still retry once within the same reservation.
- After a lost POST response, check the prepared endpoint and join a pending generation using GET only. Never issue a second POST as automatic recovery.
- Validation errors identify the field, locale and permitted length without logging generated content or credentials. Required bilingual text remains required; the prompt explicitly asks to omit unused optional fields.
- Loading copy explains the wait briefly and offers prepared examples. An interrupted request no longer implies that its credit has already been refunded.

## Verification

- 105 backend tests passed, including both cache-compatibility directions, shared-storage replay, catalog readiness, hardware/content invalidation, the real Kello/Finches shipped records, a 52-second completion, a 29+30-second validation repair, quota behavior and no duplicate read-timeout retry. Provider timing tests use controlled responses; they are not paid live-model measurements.
- 52 related frontend tests passed, including lost-response recovery, joining a pending result and one-POST-only behavior. TypeScript and targeted ESLint passed.
- Local Chrome opened Kello and Finches with generation disabled. Both rendered prepared examples; a Finches preset change updated the visible output. Backend logs contained GET playback only. Browser console reported no errors.
- Local Turbopack could not follow the existing node_modules junction outside its root; the supported webpack development/build path was used without installing packages or changing application configuration.

## Limits

This does not guarantee every new model response will be timely or valid, or that every prepared example is semantically correct. No paid model calls were made for validation. Check the exact deployed commit and production browser behavior before reporting this fix as live. Do not reuse a cache merely because its product name matches.
