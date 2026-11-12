# Independent review of the first generated Melius pilot

Date: 2026-11-12. Reviewer: creative interaction audit. Recommendation: **retain as an evaluation failure; do not promote this completion to a prepared public example.**

The generator produced a complete, editable artifact with valid cross-input coverage. It also changed the underlying product when only the advertising platform changed, and introduced unprovided promotional facts. Passing the new structural contract is therefore a useful technical result, but not a semantic-quality pass.

## Evidence and limits

Reviewed the actual saved provider response in `artifacts/demo-generator-evaluation/melius-raw.json`, the normalized result in `melius.json`, and `pilot-melius-report.json`. The report records revision `interaction-v1-2026-11-12`, one attempt, 25.81 seconds and specification SHA-256 `9be27e0258afd2f1897a49a6a18f5db33016dc651d0dfd709e3c94ff13e43145`. Raw usage records 2,490 output tokens. The parent reports the configured model as `claude-sonnet-5`; the captured raw response does not itself include a model identifier.

A network-free probe parsed the original fenced JSON, ran the compact expansion available at the initial review, and confirmed that its `interaction` equals the saved normalized `interaction`. The original completion was not manually repaired for this review. At that point, before the binding-facts extension below, `validate_interaction` accepted all four variants. No provider call was made by this reviewer.

This is a source-and-data review, not a browser or human test. CUA remains paused. The generic runtime supports editing, inclusion and ordering, but this review does not claim that a first-time visitor successfully used those controls. Source-grounding observations refer to the exact context supplied by the current evaluator, plus the official-site research recorded in [the creative audit](demo-audit-creative-2026-11-12.md).

## Separate scores

Scale: 0 = fails the criterion; 1 = partial; 2 = meets this limited criterion. No aggregate score is used because structural success must not conceal semantic failure.

| Criterion | Score | Finding |
| --- | --- | --- |
| Structural contract and finite coverage | 2 | Editor kind, three useful fields, two controls and four complete combinations; both language outputs change. |
| Fit to a creative-production task | 1 | An ad-copy draft is a plausible part of creative work. It conveys copy editing more than Melius's connected creative workflow. It cannot demonstrate media generation or quality. |
| Concrete supplied input | 1 | Platform and product category are clear, but the brief supplies no stable named product, features, audience constraints or allowed offer. |
| First usable artifact | 2 | Headline, body and CTA contain actual editable draft copy. They are more actionable than a paragraph saying the system is configured. |
| Cross-variant identity and causal isolation | 0 | A platform change silently replaces the product and its facts, so the user cannot compare channel treatments for the same product. |
| Factual scope and brief-grounding | 0 | Numeric specifications, discounts, free trials and social proof appear without being supplied in the brief. |
| Local-operation truth | 1 | The wrapper's independent-local-example disclosure and takeaway help, but scenario says Melius generates these drafts, conflating the current local interaction with a vendor action. |
| Bilingual content completeness | 2 | Both languages contain all required fields, and the same substantive problems appear in both. This is not a localization usability test. |
| First-time comprehension | Not tested | No human or current real-page session. |

## The main causal failure

The two input controls are `platform` and `product`. The product options are broad categories, B2B SaaS and Consumer Electronics. Keeping that product option fixed while changing platform produces:

| Selected category | Instagram variant | LinkedIn variant | What changed beyond the platform |
| --- | --- | --- | --- |
| B2B SaaS | TaskFlow, project management/chat/document collaboration | InsightHub, natural-language business analytics | Product name, job, features, offer and CTA all change. |
| Consumer Electronics | SonicPro wireless earbuds | DeskMate smart workstation | Product name and entire device category change. |

Both variants have different artifact text, so the new no-op validator correctly accepts the formal difference. That condition is necessary but insufficient: an input must cause the **right difference while preserving independent context**. Replacing the whole product is a cheap way for a model to satisfy output diversity.

This is not the original exact bug of a learning-app choice receiving drink copy; each branch is internally compatible with its broad category. It is still a task failure because the selected platform is presented as an independent control, and a visitor would reasonably expect the same chosen product to remain in use.

## Unprovided facts and weak grounding

The four briefs are one-line descriptions of a platform promoting a category. They do not state the following assumptions that appear later:

- TaskFlow: a 14-day free trial without a credit card.
- SonicPro: 30-hour battery life, active noise cancellation, waterproof design and a limited-time $40 discount.
- InsightHub: more than 800 customer companies and onboarding within minutes.
- DeskMate: lighting/temperature/height automation and 5,000 professional users.

An outer fictional-example label distinguishes the output from verified vendor evidence, but does not make unsupported ad promises a good drafting demonstration. The local artifact gives the visitor no way to tell which product facts were supplied and which the model improvised. A useful generative demo should demonstrate retaining a brief's constraints rather than rewarding invented promotional specificity.

The evaluator labels this run `stored_source_excerpts`. Inspection of `generation_context` shows that its three supplied excerpts concern Melius funding, founder background and revenue. They do not describe the creative-canvas workflow or any of the fictional advertised products. The metadata is technically accurate about stored excerpts being present, but it should not be interpreted as task-specific source support.

The [official Melius site](https://www.melius.com/), read during the earlier audit, describes editable connected creative work and passing results between nodes. That supports the general creative-task direction. It does not verify TaskFlow, SonicPro, InsightHub or DeskMate features, offers or customer counts.

## Is this still only switching text?

The scenario controls still choose prepared text; that is the honest scope of a data-only local example. The meaningful improvement is that the three fields are actual draft content with supported edits, inclusion and ordering, and a save operation can preserve those edits. That creates a usable local drafting task instead of claiming that a textual description is generated media.

However, this sample's only original decision is selecting a category/platform. The model has not shown that it can maintain a concrete brief while adapting the result. A visitor may understand that Melius belongs to creative tools, but this completion does not establish its distinctive workflow, native interface, media output or quality. No claim of actual user understanding is warranted.

## Proposed core prompt corrections

Do not manually fix this JSON or introduce a Melius-specific runtime branch. Update the general generation instructions and evaluate a new recorded completion:

1. **Preserve independent scenario identity.** Each product/scene/project input option refers to one fixed fictional entity. When another control changes platform, format, tone or placement, retain that entity's name, capabilities, constraints and factual assumptions. Change only content relevant to the selected dimension. Prefer one control if the second dimension cannot be kept independent.
2. **Make the brief sufficient.** A short brief should identify the fictional subject and the concrete facts/constraints allowed in its artifact. Broad category names alone are insufficient when the output invents a named product and detailed capabilities. Reuse a stable subject across related variants; do not invent one per combination.
3. **Bound promotional claims.** Do not invent customer counts, testimonials, certifications, measured performance, guarantees, trial terms, pricing or discounts to make copy persuasive. Include an offer only when it is explicitly supplied as an example input with appropriate provenance; otherwise use a neutral CTA. A generic fictional-data label is not a substitute for brief fidelity.
4. **Describe the local action precisely.** Scenario should explain that the visitor edits a prepared local draft. Explain vendor capabilities separately and only to the degree supported by context. Avoid saying the vendor just generated the current output.
5. **Assess source relevance.** Distinguish task/workflow evidence from company traction evidence. If the supplied excerpts only establish funding/founder/revenue facts, record that limitation and do not treat their presence as evidence of the modeled workflow.

These corrections complement the schema. JSON validation can enforce complete coverage and observable differences. It cannot generally prove that two renamed fictional products should have been the same entity or that an advertising claim was supported by the brief.

## Re-evaluation probes

- For each combination pair differing in exactly one input, list facts that should stay invariant and facts allowed to change. On this sample both platform-only pairs fail the identity invariant in Chinese and English.
- Extract numerical claims, offers, customer counts and named features from the output; check each against the actual selected brief. Unprovided assertions are a failure, even when the JSON validates.
- Check the scenario and action copy for who is acting: the visitor edits locally; the vendor has not run. The artifact must remain useful without asserting vendor execution.
- Apply a distinctive field edit, exclude one field, reorder remaining fields, change locale and return to the prior variant; save must match the edited visible artifact. This is the runtime behavior test, separate from model semantic quality.
- Keep the source context and model identity in the next evaluation receipt, and preserve raw completions. Re-run under existing reservation limits; never count a manually corrected completion as a model pass.
- Add a held-out creative product whose task is a cue sheet or shot plan. Passing ad-copy examples alone should not be presented as broad creative-generation quality.

The current pilot is valuable evidence: it confirms the new data contract can yield an editable artifact and exposes the next failure mode, context substitution. The release decision remains negative for this particular completion until a new generation passes the semantic probes.

## Core follow-up from this failure

After the review, the shared protocol gained optional input-option `facts`: one to five bilingual strings, each at most 120 characters. Two-control editor payloads must have at least one input whose every option declares such facts. Each variant must include all selected facts in substantive artifact values in both languages, and must not include an unselected option's exclusive facts. Identical facts also present among the selected options are exempt from exclusion. A fact appearing only in a brief or decorative field title does not bind an editor's actual content.

The Python validator and shared fixture implement this generic rule; the frontend uses the same projection and exposes the selected facts on demand and in text export. The targeted Python suite now passes 126 tests, including coverage, fact presence, wrong-context leakage, shared facts, both languages, all artifact kinds and the previously established representation boundaries. These are deterministic contract tests, not additional model runs.

The original Melius completion is now rejected because its two-input editor declares no binding facts. This is a rule change guided by an observed failure, **not** a corrected model output. It is preserved as a failed evaluation receipt. A new recorded generation must supply and preserve the facts before it can pass the updated contract.

Literal fact containment remains limited: a model might repeat a product name while still inventing unsupported features, or put the fact into an otherwise irrelevant sentence. The rule catches a useful class of context substitution; it does not certify full factual consistency, task usefulness, product capability or human understanding. The semantic review above remains necessary.
