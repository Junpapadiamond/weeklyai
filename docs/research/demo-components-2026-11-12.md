# Product tasks and icon restraint — 2026-11-12

## Scope and evidence

The user asked for multiple agents to review more than Clutch, fix examples that only swap prose, study more than ten references before deciding, and reduce generic decorative icons. Three agents reviewed creative, developer, and research workflows. The official sources were retrieved before implementation decisions; this is source and code research, not a claim of hands-on testing of all reference websites. The user subsequently redirected implementation to the shared generation core. The twelve tasks below are an evaluation corpus, not twelve custom components.

Browser access was initially unavailable, then restored. The root agent reproduced the production Melius mismatch (learning-app selection followed by a beverage ad), inspected the local hero at desktop/390/320 widths, and verified its pause state. Later release checks and pilot outcomes are recorded separately; first-time human comprehension is not measured by these agent checks.

See the creative, developer, and research audit files dated 2026-11-12 for product-specific contracts and twelve initial AI website references: Runway, Higgsfield, ElevenLabs, Gamma, Cursor, v0, Lovable, Replit, Perplexity, Notion AI, Glean, and Granola. Additional product sources were checked where the proposed behavior needed verification.

## Four component-library references

| Official reference | Observed API/example | Decision |
| --- | --- | --- |
| [shadcn/ui Tabs](https://ui.shadcn.com/docs/components/base/tabs) and [component catalog](https://ui.shadcn.com/docs/components) | Separate triggers and panels; fields, tables, native selects, code blocks and source components are distinct primitives. | Choose the component by the user's object. A table suits extracted financial records; a persistent editor and preview suit an app. Do not make every task a series of tabs. |
| [Radix Tabs](https://www.radix-ui.com/primitives/docs/components/tabs) | Controlled values, associated panels, automatic/manual activation, orientation and keyboard behavior. | Use simple native controls for small forms. Keep focus/selection behavior explicit; do not apply tab semantics to unrelated choice buttons. |
| [React Aria Table](https://react-aria.adobe.com/Table) | Row/column data with optional selection and sorting; examples retain headers and row identities. | Daloopa needs visible metric, period, unit and source relationships. Three unconnected textareas cannot communicate extraction or verification. |
| [Base UI Slider](https://base-ui.com/react/components/slider) | Value, label, track and thumb are separate; each control needs an accessible name. | Use sliders only for a real numeric cause and effect. Keep exact values visible and native keyboard controls; no decorative progress animation. |

These references inform component behavior, not a claim about which libraries the AI vendors use internally. No wholesale library installation is needed for the selected native fields, checkboxes, tables and text editors. Existing React components and CSS tokens provide the necessary primitives without a second visual system.

## Chosen tasks

- Creative: Melius product/format → coherent editable ad; Sonilo scene/layers → cue sheet; Higgsfield brief/direction → editable shot sequence; BFL subject/style/format → usable prompt draft; GasLab genre/layers → composition plan with its current waitlist destination.
- Developer: Conductor workspace/patch choices → accepted diff and local preview; Orchids feedback fields/view → working board; Lovable requirements → working sample interface; Namespace changed file → invalidated stages and cache explanation.
- Research: Exa query → relevant fictional passages with traceable matches; Daloopa period/unit → normalized comparison table and provenance; Autentic audience → matching fictional interview evidence and theme selection.

These are target task contracts. The shipped implementation uses four shared data-driven primitives (editor, records, form, review); model output chooses content and variants. Unsupported tasks remain limitations instead of being approximated by a fake run button. New interactions show the first artifact immediately, preserve per-language drafts, export current values with disclosure/sources and reset explicitly. Reading remains free of model calls. This does not imply all twelve legacy caches have been regenerated or approved.

## Global icon rule and application

Remove a repeated generic icon when its neighboring text already communicates the meaning. Product identity remains the real SmartLogo. Keep icons that carry a necessary action or state, including icon-only close, move, search, theme and favorite controls. Do not use play imagery for text-only product examples. Mobile navigation can use readable text with a visible active state instead of a row of unrelated glyphs. Existing custom HorseMark and RadarEmblem remain the brand visuals.

Apply this to demo catalog cards and quota ornament, detail headings and resource rows, preset choice arrows, artifact code-heading ornament, the homepage example entry, and mobile navigation. New task controls use labels, selected states and concrete artifacts instead of decorative icon headings.

## Release evidence

See `demo-generator-evaluation-2026-11-12.md`, the dated pilot reviews and final release report for distinct structural, semantic, browser and deployment results. A successful build or Figma layout alone does not pass the real-page gate.
