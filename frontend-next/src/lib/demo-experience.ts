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
  workspace: z.object({ kind: z.enum(["video", "image", "search", "document", "board"]), label: copy(80), initial: copy(200) }).optional(),
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
  let body;
  try { body = await response.json(); }
  catch { throw new Error("SERVICE_UNAVAILABLE"); }
  if (!body || typeof body !== "object" || typeof body.success !== "boolean") throw new Error("SERVICE_UNAVAILABLE");
  if (body.experience) {
    const result = ExperienceSchema.safeParse(body.experience.spec);
    if (!result.success) throw new Error("GENERATION_INVALID_RESPONSE");
    body.experience.spec = result.data;
  }
  return body;
}

const errorMessages: Record<string, [string, string]> = {
  DAILY_LIMIT: ["今天的生成次数已用完", "Today’s generation limit has been reached"],
  NOT_CONFIGURED: ["这个产品的演示还在准备中", "This product’s demo is not ready yet"],
  GENERATOR_NOT_CONFIGURED: ["这个产品的演示还在准备中", "This product’s demo is not ready yet"],
  PENDING: ["演示仍在生成，请稍后重新检查", "Still generating. Check back shortly."],
  GENERATION_TIMEOUT: ["AI 响应超时，请稍后重试", "The AI service timed out. Please try again shortly."],
  GENERATOR_BUSY: ["AI 服务繁忙，请稍后重试", "The AI service is busy. Please try again shortly."],
  GENERATOR_UNAVAILABLE: ["AI 服务暂时无法连接", "The AI service is temporarily unavailable"],
  GENERATION_INCOMPLETE: ["AI 返回的内容不完整，请重新生成", "The AI response was incomplete. Please generate again."],
  GENERATION_INVALID_RESPONSE: ["这次生成的演示无法使用，请重新生成", "The experience did not pass validation. Please generate again."],
  SERVICE_UNAVAILABLE: ["连接暂时中断，请重新检查生成结果", "Connection interrupted. Check again for the result."],
  STORAGE_UNAVAILABLE: ["演示暂时无法保存，请稍后重试", "The experience could not be saved. Please try again shortly."],
};

export function demoErrorMessage(error: string): [string, string] {
  return errorMessages[error] ?? ["这次生成没有完成，请稍后重试", "This generation did not finish. Please try again shortly."];
}
