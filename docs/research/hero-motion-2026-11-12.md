# Hero radar motion — 2026-11-12

The home hero keeps its featured product and real `SmartLogo`. The change makes the existing HorseMark and radar easier to see: a warm, high-contrast horse, a red sweep, and three fixed signals that respond as the sweep reaches them. It does not change product facts, ranking, discovery dates, sources, or prepared-example eligibility.

## User task and boundary

| Gate | Contract |
| --- | --- |
| User task | Discover one featured AI product, open its details or prepared example, or search for another use case. |
| Input | Existing product links and search field; click the horse itself to pause/resume the illustration. |
| First visible result | The existing real product identity remains the focal content; the radar introduces the brand visually. Pause immediately freezes the illustration. |
| Evidence | Product text/logo/source retain the existing data path. Radar signals are a deterministic brand illustration, **not live discoveries, measured product events, or vendor activity**. There are no generated counts, real-time status labels, fake product logos, or data claims. |
| Next step | Existing View details / Try example / Search actions remain actionable. Motion is never required to use them. |

## Code and behavior

- `frontend-next/src/components/brand/radar-emblem.tsx`: original HorseMark component retained; fixed coordinates; client pause state; IntersectionObserver and document visibility pause background/offscreen work. Static callers such as the recovery page receive no motion or control by default.
- `frontend-next/src/components/home/chinese-home-intro.tsx`: opts into animation and provides Chinese/English accessible pause/resume names. The earlier removal of the decorative Play icon remains intact.
- `frontend-next/src/styles/hero-motion.css`: existing navy/ivory/coral palette, 9.6-second clockwise sweep, signal offsets of 0 / 2.4 / 6 seconds, and a small acquisition bracket. The only animated properties are transform and opacity; no layout animation, canvas loop, random particles, timers, or new motion dependency.
- Reduced-motion preference renders a complete static illustration with no motion button. Otherwise HorseMark is the native button, with a changing accessible name, Enter/Space activation, and visible keyboard focus; there is no separate pause/play glyph. The hit target is at least 44 × 44 CSS pixels at all sizes. Narrow screens reserve heading space for the radar while the product identity uses the full width below it; content and search remain independent of the illustration.
- The root integration imports `hero-motion.css` after `editorial.css`; this file intentionally overrides only hero/radar selectors. `brand.css`, `base.css`, product facts, and company logo data were not edited by this task.

## Current deliverable: horse control in NYU Software Ninjas

The user chose **NYU Software Ninjas**, the education plan returned by `whoami` as `team::1075815332585348015`. Both files below were created with that exact plan key. The earlier personal drafts remain intact; file sharing was not widened and nothing was published.

- [Editable Design review](https://www.figma.com/design/ShKOiFymrFH8EvIdqTIGHK?node-id=1-351), frame `1:351`, 792 × 1083. [Component family](https://www.figma.com/design/ShKOiFymrFH8EvIdqTIGHK?node-id=1-350), set `1:350`: Scanning `1:211`, Paused `1:240`, Focus `1:268`, Compact `1:296`, Reduced motion `1:324`. Original HorseMark component: `1:134`.
- Scanning/Paused/Focus/Compact contain linked **Simple Design System Icon Button — Neutral / Default / Medium** instances (`1:233`, `1:262`, `1:290`, `1:318`). The button container is transparent and its instance-swap slot contains the repository's HorseMark. No Pause/Play library glyph remains. Reduced motion has a static HorseMark and zero controls. The compact control measures 45.36 × 45 pixels.
- Four primitive colors and four semantic aliases retain explicit scopes and web code syntax. All five review labels use one Inter Medium text style and report `missingFont=false`. Scanning stores a 9.6-second clockwise native rotation plus staggered echo-opacity tracks. This is editable motion data; the screenshot establishes resting appearance, not playback.
- An actual screenshot exposed the library's inherited 20-pixel icon slot making the horse too small. Setting the nested slot to fill its transparent button corrected it without detaching the library instance. The final screenshot was downloaded and visually inspected after the correction; all five states show the horse and unclipped labels. Native DOM keyboard/ARIA behavior belongs to the production component and Make prototype, not to a static Figma frame.

![NYU hero: horse is the motion control](../../artifacts/hero-motion/hero-horse-nyu.png)

The production `RadarEmblem` now uses HorseMark itself as a native button. Its accessible name changes between pause/resume, browser-native Enter/Space activation is retained, and keyboard focus has a visible outline. A subscribed reduced-motion preference renders the static mark without a button. Root's 320-pixel heading/identity layout repair remains intact. Signals remain deterministic brand illustration, with no new product facts or claims of live discovery.

[NYU Make exploration](https://www.figma.com/make/jB3HVvliW0OtWW1e4N8a37), node `1:6`, received the updated two-file public export (`index.html`, `kora-logo.png`) from `artifacts/hero-motion/make-nyu-source/`. The current `prepare-make.cjs` reproduces that export. The ZIP was built and inspected in the same WSL shell as the uploader; upload exited 0 and `send_code_to_figma` returned **`status: imported`**. The receipt is recorded in `artifacts/hero-motion/make-nyu-import-receipt.json`. The tool explicitly says **No Code agent ran** and preview **not_verified** at import time. The root agent owns subsequent browser verification and the user's requested actual AI refinement prompt; this subagent did not submit a duplicate prompt. The prototype is a design exploration, not a claim of exact production layout.

The earlier editor-access block below is historical: after the user logged in, the root agent actually observed the **personal** Make hero iframe running, status **Running**, and enabled **Prompt for AI agent**. Send was disabled only while its input was empty. That resolved access to the personal prototype; it is separate from validation of the new NYU file.

## Earlier personal Design iteration (superseded)

The Figma use, component-library, and motion skills were used. An initial narrow radar/motion-control search did not match. Following the user's explicit request to use the material library, a concrete `Icon Button`, `Pause`, and `Play` search found real Simple Design System assets. All four controls now use linked instances of those library components; the brand horse/radar remains the repository's own geometry. The artifact is editable vector/component content rather than a screenshot pasted into a frame.

- [Review frame](https://www.figma.com/design/CwfXemf7jlH7zWiqIsjRCz?node-id=12-133), node `12:133`, 792 × 730.
- [Hero component family](https://www.figma.com/design/CwfXemf7jlH7zWiqIsjRCz?node-id=12-132), node `12:132`: `State=Scanning`, `Acquired`, `Paused`, `Compact`. The first three are 360 × 300; Compact is 108 × 90, with a full-size control.
- Original HorseMark component: `12:15`, using the repository SVG paths. Its nested instances remain linked.
- Four primitive and four semantic alias color variables in `Darkhorse / Hero`, with explicit scopes and `var(--hero-*)` web code syntax. Review labels use one Inter Medium text style; all four report `missingFont=false`.
- Scanning variant has editable 9.6-second rotation and staggered scale/opacity echo tracks. Static variants are suitable for paused/reduced-motion review. Figma's timeline stores one cycle; the website loops that cycle until paused.
- Earlier nodes `2:27` (Radar acquisition) and `2:36` (Example changed) were left unchanged.

Final Figma screenshot was rendered, downloaded, and visually inspected after the compact control adjustment:

![Editable hero radar variants](../../artifacts/hero-motion/hero-radar-variants.png)

### Actual library adoption

Source: the **Simple Design System** library returned by Figma `get_libraries` / `search_design_system` (source classified by the tool as `community`). No claim is made that search results alone were applied: the following assets were actually imported and instantiated.

| Asset | Published component key | Adopted instances |
| --- | --- | --- |
| Icon Button — Neutral / Default / Medium | `8b9eae54bbaf04a3bebc193f9a4a757c0d5612ab` | `15:206`, `15:211`, `15:215`, `15:219` |
| Pause | `9c41a395be389f99c76dafadefb9fbdcab86bb6b` | Nested via the Icon Button's INSTANCE_SWAP property in the three running states |
| Play | `6ff2733ec1af4bdc65c37e07e902f7a333b2dc7a` | Nested via INSTANCE_SWAP in the paused state |

Adaptations: preserve the 44-pixel library button, round its surface to the existing radar control, bind surface/line/ink to the hero palette, and keep nested icon canvases transparent. The library instances were **not detached**. HorseMark and product logos were not replaced. A visual check caught an accidental filled icon canvas during recoloring; it was corrected and the final screenshot below was rendered and inspected afterward.

![Hero variants with actual linked SDS controls](../../artifacts/hero-motion/hero-radar-library-variants.png)

### Actual Figma Make attempt and result

This round created a **new** [Figma Make file](https://www.figma.com/make/yGkRLQAHOj9TLbhxEw1sf9), node `1:6`; this is not the older Make homepage linked elsewhere in the project. The `figma-code-workflows` and file-creation skills were used, followed by the real `send_code_to_figma` upload/import workflow.

The import contains a static export of the repository's actual RadarEmblem markup/current hero CSS, local pause/visibility/language controls, the current public Kora Systems catalog copy and logo, and SVGs exported from the adopted SDS Pause/Play controls. Source files are under `artifacts/hero-motion/make-source/`; preparation is reproducible via `artifacts/hero-motion/prepare-make.cjs`. Only these four public prototype files were uploaded: `index.html`, `kora-logo.png`, `pause.svg`, `resume.svg`. No repository credentials, backend, environment file, or private dataset was included.

Exact progression:

1. The first upload attempt failed before file transfer (`exit 26`): the execution shell used WSL `/tmp`, while the ZIP had been written to Windows `C:/msys64/tmp`. Import was not called.
2. Fresh upload instructions were obtained; the archive was verified in that same shell. The second upload returned HTTP 400 because the execution wrapper expanded `$checksum` before bash, sending an invalid value. Import was again not called.
3. After explicit continuation from the parent, fresh instructions were obtained again. The same archive's SHA-256 was computed locally and substituted as the literal intended checksum; all issued authentication fields and destination remained unchanged. Upload exited 0; Figma returned **`status: imported`** with an import receipt. See `artifacts/hero-motion/make-import-receipt.json` for the sanitized result.

This is a **real Make code import**, not a Make AI prompt generation. The tool explicitly reported **“No Code agent ran”** and **`preview.status: not_verified`**. The connected tool inventory exposed no `send_prompt` action. `open_figma_mcp_app_in_thread({fileKey:"yGkRLQAHOj9TLbhxEw1sf9",nodeId:"1:6"})` returned `content:[]` and `structuredContent:{surface:"thread"}`, with no viewer URL. This subagent's attempt to inspect that surface returned `Browser is not available: mcpapps`.

The parent then **actually opened the new Make URL in its working IAB**. The visible result was **“Couldn't load Make” / “You need to be an editor to preview this Make (M9)”**, with **Sign up / Continue with Google** controls. **Prompt for AI agent** and **Send** were disabled. Thus the confirmed result is source import plus a browser-observed editor-access block—not a working preview and not a successful AI generation. No file permissions were expanded and the file was not published. Imported source and configured preview scripts alone do not establish that the preview ran successfully.

At this earlier stage the linked SDS controls were applied only in the personal Design family and Make export. The current NYU iteration and production code supersede the standalone glyph design with the horse control described above.

## Verification and limits

- Focused ESLint for the two edited TSX files passed.
- TypeScript `--noEmit --pretty false` passed against the shared worktree at the time of this change.
- Figma screenshot review confirms visible horse/rings/controls, unclipped state labels, linked instances, and the 44-pixel compact control. Structural inspection confirms the four variants, font availability, token aliases, and stored motion tracks. A static screenshot is not playback verification.
- This subagent attempted a fresh in-app browser tab after the parent reported restored browser access; it returned `Browser is not available: iab`. No native browser fallback was attempted. Actual page playback, pause/resume, reduced-motion, and 1440/390/320 viewport checks are assigned to the parent's working browser before release. No first-time user comprehension study has been performed.


## Root browser verification and actual NYU Make AI run

The root opened the imported NYU Make in the authenticated browser and saw its runnable iframe, `Running` status and enabled `Prompt for AI agent`. Two actual AI prompts were submitted through the Make UI, with no publish or sharing changes:

1. Refine the imported hero while preserving navy/parchment/coral, original HorseMark, real Kora logo, horse-only motion control, accessible behavior, comfortable English and responsive layouts. The UI reported `Agent task started`, then a completed edit and **Make version 1**, commit `69a2f75f5c2437df195acba77f53cb10a94e19c7`. Its generated output used a 13.5-second scan, softer depth/grid treatment and a restructured responsive layout. Make reported its own format/build checks passing; those are separate from this repository's checks.
2. Root's actual English preview inspection found the product heading still had **-2.13174px** tracking, despite the AI summary. A corrective prompt explicitly named that computed-style failure. Make completed **version 2**, commit `daaf8425fcdbb63a60e353ae1b81a491776c5df1`. Root switched the reloaded preview to English and measured heading/body tracking `normal`, body font 15.36px and line-height 25.344px (1.65).

Root actually clicked the horse to pause, observed pressed state, resumed with Space, and switched languages. The preview was also opened from its observed iframe URL for 320px/390px checks: no horizontal document overflow was observed. The 390px hero measured about 814px tall; its large stacked radar consumes substantial mobile space. Therefore the production page retains its compact mobile layout and existing button/edge treatment, adopting only the calmer 13.5-second scan and localized atmospheric depth. Signal delays are adjusted to 3.375 / 8.4375 seconds to retain angular timing. Production does not copy the Make page wholesale. The editable Figma Design motion sample retains its earlier 9.6-second cycle as design history.

Screenshots: `artifacts/hero-motion/make-nyu-ai-final.png` (actual editor + final English preview), `make-nyu-mobile.png` (390px). These ignored local artifacts are evidence attachments, not deployment assets.

After the second completed prompt, Figma displayed: **You're out of AI credits in NYU Software Ninjas Education plan until they reset on Nov 30.** No further prompt, paid upgrade, account switch or quota workaround was attempted. The NYU Make tab remains available as the user-facing deliverable. This is a completed Make AI trial and browser-inspected prototype, not merely a source import.
