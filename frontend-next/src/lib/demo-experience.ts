import { z } from "zod";

const copy = (max: number) => z.object({ zh: z.string().trim().min(1).max(max), en: z.string().trim().min(1).max(max) });
const step = z.object({
  id: z.string().min(1).max(40), widget: z.enum(["choice", "review", "dial", "compare", "app"]),
  title: copy(80), instruction: copy(300), example_data: z.literal(true),
  options: z.array(z.object({ id: z.string(), label: copy(80), output: copy(700) })).min(1).max(4),
  app_kind: z.enum(["timer", "tasks", "expenses"]).optional(),
  dial: z.object({ min: z.number().int().min(0), max: z.number().int().max(1000), initial: z.number().int(),
    factor: z.number().int().min(1).max(100), unit: copy(40), result_label: copy(80) }).optional(),
}).superRefine((value, ctx) => {
  if (value.widget === "app" && !value.app_kind || value.widget === "dial" &&
    (!value.dial || value.dial.min >= value.dial.max || value.dial.initial < value.dial.min || value.dial.initial > value.dial.max))
    ctx.addIssue({ code: "custom", message: "Invalid interactive control" });
});
export const ExperienceSchema = z.object({
  version: z.literal(2), confidence: z.literal("illustrative"), tier: z.enum(["workflow", "concept"]),
  headline: copy(120), scenario: copy(400), steps: z.array(step).min(3).max(6), takeaway: copy(500),
  sources: z.array(z.object({ label: copy(100), url: z.string().url().refine(url => {
    const parsed = new URL(url);
    return ["https:", "http:"].includes(parsed.protocol) && !parsed.username && !parsed.password;
  }) })).min(1).max(6),
}).refine(value => new Set(value.steps.map(s => s.id)).size === value.steps.length, "Duplicate steps");
export type Experience = z.infer<typeof ExperienceSchema>;
export type ExperienceEntry = { spec: Experience; cache_key: string; origin: "curated" | "pregenerated" | "ai"; generated_at: string };
export type DemoQuota = { limit: number; used: number; remaining: number; site_remaining: number; resets_at: string };
export type DemoResponse = { success: boolean; state?: string; error?: string; experience?: ExperienceEntry;
  quota: DemoQuota | null; generation_available: boolean };

export async function readDemo(response: Response): Promise<DemoResponse> {
  const body = await response.json();
  if (body.experience) body.experience.spec = ExperienceSchema.parse(body.experience.spec);
  return body;
}
