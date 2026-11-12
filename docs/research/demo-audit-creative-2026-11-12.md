# Creative demo research — 2026-11-12

Status: implementation approved after the combined review exceeded ten distinct references. Browser work remains paused; verification in this run is limited to source and automated checks until a safe browser is available.

## Evidence boundary

Official pages below were retrieved on November 12. Browser preflight returned no available in-app browser or Chrome connection. Browser work was then stopped as coordinated by the parent agent; no workaround or security-check bypass was attempted. This report is official-source research and current-source inspection, **not a live usability test or screenshot audit**. Existing screenshots from November 9 are not evidence for this run.

Gamma is absent from the current featured catalog. ElevenLabs and Runway have catalog records but no committed prepared cache. The prepared creative candidates are therefore Higgsfield, Melius, Sonilo, and Black Forest Labs, with GasLab as an additional audio case. No generation credits are needed to review these examples.

## Four official references

| Reference | Observed public structure | Concrete design lesson for WeeklyAI | What this does not establish |
| --- | --- | --- | --- |
| [Runway Creative](https://runway.com/product), [Workflows](https://runway.com/workflows) | The product page separates concrete transformations such as removing an element, relighting, or changing a backdrop. Workflows distinguishes media/text inputs, model transformations, and outputs; it describes running one node separately from the entire workflow. | Show the input that remains in use beside the result. A changed input must affect subsequent work. Use task names rather than a generic configuration sequence. | Marketing examples and documentation do not prove the quality of a generated result or our ability to reproduce the vendor UI. |
| [Higgsfield Cinema Studio](https://higgsfield.ai/generate), [Help Center](https://higgsfield.ai/creator-hub/help-center) | The public app shell separates projects, generations, elements, and favorites. The help center routes by creative goal and distinguishes tools from models. | A visible creative artifact should have an identity and retained context. Separate choosing a creative direction from arranging the resulting shot plan. | The fetched app shell does not expose authenticated generation controls; those controls are not claimed as tested. |
| [ElevenLabs Text to Speech](https://elevenlabs.io/text-to-speech) | The public example groups language, voice, use case, text entry, and a speech-generation action. Other sections identify delivery controls such as speed and pacing. | For an audio concept, expose the actual script or cue sheet being shaped. Keep context and audible output distinct; a playback icon is appropriate only for playable audio. | WeeklyAI has no vendor-generated audio in these examples. A cue-sheet interaction cannot demonstrate speech quality. |
| [Gamma Presentations](https://gamma.app/products/presentations), [Gamma](https://gamma.app/) | The public product pages distinguish an initial outline, theme/layout choices, and later editing. The overview explicitly places iteration beside the deck and distinguishes content formats. | Present an editable, coherent artifact with surrounding choices, rather than isolated paragraphs. A layout change should visibly alter that artifact while retaining its content. | No logged-in Gamma editor was tested during the text retrieval. |

These are four distinct vendor references, not a claim that every linked page is a separate design system.

## Product-specific official cross-checks

Four additional official sites were checked to keep the proposed task aligned with the actual product:

| Official source | Retrieved evidence | Consequence for the candidate |
| --- | --- | --- |
| [Melius](https://www.melius.com/) | Its public FAQ describes a creative canvas with editable prompts and connections passing one node's output into the next, including downstream reruns and side-by-side branches. | A selected product remaining consistent across output formats is essential to the illustration. A pair of unrelated text tabs is a poor representation. |
| [Sonilo](https://sonilo.com/) | The public creation area pairs video upload, a prompt and a soundtrack action. Its FAQ describes keeping, adjusting, replacing or layering original audio. | Preserve the selected scene while changing its cue layers. A local cue sheet must not be presented as rendered music, measured timing, or commercially licensed output. |
| [GasLab](https://gaslab.ai/) | The homepage says Opening soon and offers a guest list. | Do not imply visitors can currently generate music immediately on the platform. The next action is the official launch/availability page; attribution examples cannot establish detected authorship. |
| [Black Forest Labs](https://bfl.ai/) | The public page separates image/video/audio examples and offers distinct playground, API and open-weight paths. | Label the local result as a prompt draft and link to the official playground path. A text-only illustration cannot establish visual output quality. |

This report therefore contributes eight distinct official vendor sites. The initial requested four are design references; the additional four ground the specific repair candidates. All observations above come from retrieved page content, not a running authenticated editor.

## Prepared-content findings to verify in the browser

| Product / route | Reproduction from current stored data | Why it obstructs understanding | Candidate fix |
| --- | --- | --- | --- |
| Higgsfield, available from `/demo` | Four independently selected sections have no dependencies. Creative direction and handoff choices change descriptions separately from the prepared shot sequence. | A visitor may infer that selecting cinematic close-ups changes the plan, although the renderer only swaps the selected section's text. | A single retained product brief and editable three-shot plan; creative direction changes the actual shot descriptions, and any sequence edits persist. Explicitly a production plan, with no fake video player. |
| Melius, `/product/p_85288867790377a1` | Choose Learning app in `brief`; both options in `format` remain energy-drink copy/storyboards. There are no `when` dependencies. | The resulting advertisement is for a different product, so the user cannot reason about what their choice did. | One product selection feeding headline, audience, CTA and storyboard; changing ad format changes the corresponding prepared artifact. Keep source attribution and fictional-example status. |
| Sonilo, `/product/p_2911d03ea39fe678` | Choose Action Sequence; `audio_layers` remains independently fixed to electronic music or sunset-beach ambience. | The purported sound adjustment does not refer to the selected scene. Nothing can be heard, and the output title still says Generated Audio Plan. | A retained scene with a visible local cue sheet. Enable/disable named music, ambience and effects entries for that scene. Clearly label a sound plan and omit playback until real audio exists. |
| Black Forest Labs, `/product/845` | Four sections contain only text choices and statements such as Configured. The output mentions a final page and handoff download that do not match the current focused renderer. | Configuration wording implies an image tool has run; the visitor never sees a concrete image or useful assembled prompt. | One prompt-building surface with subject, style and intended format visibly assembled into a copyable prompt; retain official image examples only when sourced and appropriate. Do not fabricate generated images. |
| GasLab, `/product/p_eaee8b9d8e3a7085` | Choose Ambient Electronic; `attribution_check` still describes an 8-bar techno segment. | A fictional attribution report appears causally related to a previous choice but is not. It also cannot demonstrate music quality. | Keep a concrete composition/cue plan connected to its selected genre. Treat attribution as a separate illustrative record, avoiding a claim of detected authorship or generated audio. |

## Icon and logo direction

Retain each real product logo through SmartLogo. The main controls should be named after the user's creative action and rely on typography, grouping, order and visible state. Repeated sparkle/play/file ornaments do not clarify a text-only result. Keep conventional icons only when they convey a real action, such as copy, move, or an external link; never add a play icon to an artifact with no playable media.

## Proposed task contracts

- **Shot planning:** a PM compares how one product brief could become a short video. Inputs are the prepared brief and creative direction; the first result is the complete shot plan. It is an independent proposed plan, and the next action is to rearrange/copy it or try the official service.
- **Ad drafting:** a PM compares ads for the selected product. Inputs are product and delivery format; the first result is a coherent prepared headline/CTA or storyboard. It is fictional ad copy, and the next action is to refine the local draft or visit the vendor.
- **Sound planning:** a PM sees which audio cues fit the chosen clip. Inputs are the scene and included layers; the first result is the scene-specific cue sheet. It is a local planning illustration without audio generation, and the next action is to revise/save the plan or use the real audio tool.
- **Image prompting:** a PM assembles a reproducible image brief. Inputs are subject, style and format; the first result is a readable, copyable prompt containing those inputs. It is a local prompt draft, and the next action is to copy it into the official tool and inspect the actual output there.

## Selected implementation contracts

The selected repair uses five local task-specific editors, retaining the common product logo, independent-example disclosure, source, reset and text export in the parent wrapper. No new package or decorative icon set is needed.

| Product ID | Task and input | First visible editable artifact | Evidence and next action |
| --- | --- | --- | --- |
| `p_85288867790377a1` — Melius | Compare a prepared product campaign using product and ad-format choices. | Matching headline/body/CTA or a three-shot script for that same product. | Independent ad draft; edit/save it or open Melius. |
| `p_2911d03ea39fe678` — Sonilo | Plan sound for a selected fictional clip by choosing the scene and enabled music/ambience/effects layers. | A scene-specific cue sheet with editable cue descriptions and proposed timing. | Local sound plan, no generated audio; edit/save or open Sonilo. |
| `845` — Black Forest Labs | Assemble an image brief from subject, style and output format. | The assembled prompt, available for direct editing and copying. | Local prompt draft, no generated image; copy/save or open BFL. |
| `p_eaee8b9d8e3a7085` — GasLab | Arrange a fictional track using genre, tempo and section lengths. | Editable arrangement sections and a transparent local 4/4 beat-duration calculation. | Composition plan only, no music or attribution detection; save or inspect official availability/guest list. |
| `933` — Higgsfield | Shape an ad shot plan from product name, creative direction and placement. | A complete editable three-shot plan, with working reorder controls. | Independent production plan, no rendered video; save or open Higgsfield. |

Inputs and edited output text persist across language switches, with separate text drafts for each language. Changing a task-defining selection produces the corresponding coherent prepared artifact; returning to a prior selection restores that selection's edits. Literal user text is never interpreted as a live vendor request.

## Acceptance invariants for the later implementation decision

1. Melius learning-app input must never yield beverage claims, a drink bottle, or green-tea storyboard text. Product selection must propagate through every offered format and any export.
2. Sonilo scene selection must remain visible and determine the cue descriptions. A parkour clip must not gain sea waves solely because the generic ambience option was selected. Layer controls should change the actual included cue rows.
3. GasLab must not label an ambient choice as a techno source report or claim the current official site is an immediately available generation product. Any attribution illustration needs its own stated example context.
4. Black Forest Labs controls must modify the assembled prompt shown to the visitor; there should be no false configured/generated/completed state or nonexistent final-page instruction.
5. Higgsfield direction and sequence choices must affect the same retained shot plan. Rearrangement and copy/export must use that visible plan, preserving the distinction between a plan and media output.
6. Keep real logos. Remove ornamental repeated generic icons; use controls and visible content changes to explain action. No fabricated thumbnail, waveform, play affordance or vendor-output claim is an acceptable substitute for unavailable media.
