# Generated interaction contract v1

Decision: replace product-ID-specific additions with a small data-only runtime. Existing v2 caches remain readable and explicitly legacy; newly generated `interactive-v1` output must contain `interaction`. No generated JS/HTML, network actions, or credentials.

## Envelope

Model output: `{format:"interactive-v1",headline:Copy,scenario:Copy,takeaway:Copy,interaction:Interaction}`. Copy on the wire is `[zh,en]`; normalized Copy is `{zh,en}`. Server injects version=2/confidence=illustrative/tier/sources and creates one compatibility snapshot step. New renderer dispatches on interaction.kind before legacy product routes. No name/ID logic.

`Interaction = {kind:"editor"|"records"|"form"|"review",input_label:Copy,output_label:Copy,inputs:Input[],variants:Variant[]}`

`Input = {id:string,label:Copy,options:{id:string,label:Copy,facts?:Copy[]}[]}`

`Variant = {when:{[inputId]:optionId},brief:Copy,artifact:Artifact}`

Inputs: 0–2, each 2–3 options; cartesian product maximum 4. Variants: exactly one for every combination (one empty when if zero inputs). IDs unique bounded alphanumerics/_/-. Every variant must have the same artifact kind's shape. Changing one input must change serialized artifact content in each language, not only its brief. All variant contexts are complete; there is no partially retained downstream prose.

Optional facts are 1–5 short bilingual pairs, <=120 characters per language. An editor with two inputs must bind every option of at least one input. Selected facts must appear literally in substantive artifact values; unique unselected facts must be absent. A fact shared with a selected option is permitted. Review checks every possible patch subset (at most 16), not just the original base. Records branch comparison excludes collapsed evidence-only changes. This is literal consistency, not semantic truth checking or numerical source entailment.

## Artifacts

- **editor**: `{fields:{id,label:Copy,value:Copy}[]}` with 2–6 fields. Users edit the full artifact, include/exclude fields and reorder them. Appropriate for an ad, prompt, shot plan or cue sheet. No claim of generated media.
- **records**: `{columns:{id,label:Copy,type:"text"|"number"|"select",unit?:Copy,options?:{id,label:Copy}[]}[],rows:{id,cells:{[columnId]:Copy|number|string},evidence?:{text:Copy,quote:Copy}}[],view:"table"|"board",group_by?:string,calculation?:{op:"sum"|"difference"|"count",column?:string,left?:string,right?:string,label:Copy}}`. 2–5 columns, 2–6 rows. Text cells are Copy, numbers finite, select cells are option IDs. Board groups by a select column. Users search/select records, edit numeric cells or select statuses; read evidence with exact quote highlighting. Calculation uses current numeric cell values (difference=left minus right; sum uses all rows; count uses selected rows). No arbitrary formula strings. Units must be explicit for numeric columns, source evidence remains available and fictional.
- **form**: `{title:Copy,fields:{id,label:Copy,type:"text"|"email"|"number",required:boolean}[],submit_label:Copy,confirmation:Copy}`. 2–5 fields. Users toggle inclusion/required state, edit title/labels, and submit the local preview using native validation. Never send form values anywhere; confirmation says local sample.
- **review**: `{base:Copy,patches:{id,label:Copy,before:Copy,after:Copy}[]}`. 2–4 non-overlapping patches. Each before must occur exactly once in base in both languages; after differs. Apply/reject toggles create an actual merged text preview. Never execute model code or claim tests ran.

## Bounds and validation

Copy labels <=80 chars/language; brief <=300; field value/evidence/base <=1400; patch before/after <=700; outer existing envelope bounds unchanged. Reject unknown keys, duplicate IDs, missing or extra cells, unresolved references, invalid board columns, invalid numbers/units, quotes absent from evidence, overlapping patches, no-op outputs and unreachable variants. Model errors get at most the existing one bounded repair; do not fabricate a fallback and report success.

The renderer preserves independent drafts keyed by variant and language; switching language never remounts the entire task. Reset is explicit. Save includes current values, all selected inputs, disclosure and public sources. Native controls preserve keyboard and focus behavior. Source provenance and fictional data are distinct from model quality and human comprehension.

## Evaluation

Twelve products are a benchmark corpus, not a product-ID allowlist. Evaluate existing stored examples as a baseline, generated schema validity, deterministic interaction probes, semantic fit/source support, and human comprehension separately. Include held-out renamed/reordered fixtures. Real provider runs use DemoStore reservations with a stable evaluation actor and separate evaluation cache keys. On 2026-11-12 the user explicitly authorized a total of nine local evaluations, including the original three; the runner alone passes user_limit=9 and keeps a persistent attempt ledger in which failures are not refunded. Production limits and the global cap remain unchanged. No automatic publication or budget reset.

Repair must retain the first parseable supported interaction kind and the original task. An invalid form cannot become a prose editor merely to pass schema. At most two provider calls remain permitted per evaluation, with a 3,600-output-token ceiling per call.
