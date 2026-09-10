import { z } from "zod";

/**
 * Mirror of backend/app/services/demo_spec.py. The backend is authoritative;
 * this exists so the client refuses to render anything that would not have
 * passed there — a demo served from a stale cache or a hand-edited file gets
 * rejected here rather than rendering a half-built widget.
 *
 * Prose is always a {zh, en} pair. Literal values a reader copies — a search
 * query, a product or competitor name — stay plain strings.
 */

const Loc = z.object({ zh: z.string().min(1), en: z.string().min(1) });
export type LocalizedText = z.infer<typeof Loc>;

/** A value the reader sees: sourced, or visibly an example. Never neither. */
const Datum = z
  .object({
    label: Loc,
    value: Loc,
    evidence_ref: z.number().int().nullable().default(null),
    is_example: z.boolean().default(false),
  })
  .refine((d) => d.evidence_ref !== null || d.is_example, {
    message: "every value must cite evidence or be flagged as an example",
  });
export type Datum = z.infer<typeof Datum>;

const QueryResponse = z.object({
  type: z.literal("query_response"),
  mode: z.enum(["live", "cached"]),
  endpoint_id: z.string().nullable().default(null),
  allow_free_input: z.boolean().default(false),
  presets: z.array(z.object({ query: z.string(), response: Loc })).min(1).max(5),
});

const SplitCompare = z.object({
  type: z.literal("split_compare"),
  input: z.string(),
  left: z.object({ title: Loc, body: Loc }),
  right: z.object({ title: Loc, body: Loc }),
  takeaway: Loc,
});

const Pipeline = z.object({
  type: z.literal("pipeline"),
  stages: z.array(z.object({ name: Loc, input: Loc, output: Loc })).min(2).max(6),
});

const SpecMatrix = z.object({
  type: z.literal("spec_matrix"),
  subject: z.string(),
  competitors: z.array(z.string()).min(1).max(3),
  rows: z.array(z.object({ spec: Loc, values: z.array(Datum) })).min(3).max(10),
});

const ScenarioBranch = z.object({
  type: z.literal("scenario_branch"),
  branches: z.array(z.object({ persona: Loc, situation: Loc, outcome: Loc })).min(2).max(4),
});

const HotspotShot = z.object({
  type: z.literal("hotspot_shot"),
  shot_url: z.string().url(),
  hotspots: z.array(z.object({ x: z.number().min(0).max(100), y: z.number().min(0).max(100), note: Loc })).min(2).max(6),
});

const ParamDial = z.object({
  type: z.literal("param_dial"),
  param: Loc,
  min: z.number(),
  max: z.number(),
  step: z.number().positive(),
  unit: z.string(),
  formula_note: Loc,
  outputs: z.array(Datum).min(1).max(4),
});

const Transcript = z.object({
  type: z.literal("transcript"),
  turns: z.array(z.object({ speaker: z.enum(["user", "product"]), text: Loc })).min(3).max(12),
});

export const WidgetSchema = z.discriminatedUnion("type", [
  QueryResponse,
  SplitCompare,
  Pipeline,
  SpecMatrix,
  ScenarioBranch,
  HotspotShot,
  ParamDial,
  Transcript,
]);
export type Widget = z.infer<typeof WidgetSchema>;

export const DEMO_TIERS = ["sandbox", "simulation", "concept", "tour"] as const;
export type DemoTier = (typeof DEMO_TIERS)[number];

export const DemoSpecSchema = z
  .object({
    version: z.literal(1),
    product_slug: z.string().min(1),
    product_name: z.string().min(1),
    tier: z.enum(DEMO_TIERS),
    title: Loc,
    premise: Loc,
    steps: z
      .array(z.object({ id: z.string(), label: Loc, narration: Loc, widget: WidgetSchema }))
      .min(3)
      .max(5),
    evidence: z.array(z.object({ claim: z.string(), source_url: z.string().url() })).default([]),
    confidence: z.enum(["verified", "inferred", "illustrative"]),
    vendor_status: z.enum(["none", "contacted", "corrected", "key_supplied"]).default("none"),
    generated_at: z.string().default(""),
    model: z.string().default(""),
    reviewed_by: z.string().nullable().default(null),
  })
  // A reconstruction can never present itself as verified.
  .refine((s) => s.tier !== "simulation" || s.confidence === "illustrative", {
    message: "a simulation must be marked illustrative",
  })
  // Live mode without a registry id would mean a URL came from somewhere it shouldn't.
  .refine(
    (s) =>
      s.steps.every(
        (step) => step.widget.type !== "query_response" || step.widget.mode !== "live" || !!step.widget.endpoint_id
      ),
    { message: "a live query widget must name a registered endpoint" }
  );

export type DemoSpec = z.infer<typeof DemoSpecSchema>;

/** Tiers that are reconstructions rather than the real product. */
export function isReconstruction(spec: Pick<DemoSpec, "tier">): boolean {
  return spec.tier === "simulation";
}
