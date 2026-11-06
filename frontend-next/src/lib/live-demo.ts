import { z } from "zod";
import type { Product } from "@/types/api";

export const DemoSpecSchema = z.object({
  kind: z.enum(["timer", "tasks", "expenses"]),
  title: z.string().trim().min(1).max(60),
  description: z.string().max(180),
  accent: z.enum(["rose", "emerald", "amber"]),
  minutes: z.number().int().min(1).max(180),
  items: z.array(z.string().trim().min(1).max(80)).max(8),
});

export type DemoSpec = z.infer<typeof DemoSpecSchema>;
export type DemoKind = DemoSpec["kind"];
export type DemoAccent = DemoSpec["accent"];

export function supportsLiveDemo(product: Pick<Product, "website" | "needs_verification" | "is_hardware">): boolean {
  if (!product.website) return false;
  try {
    const url = new URL(product.website);
    return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password;
  } catch {
    return false;
  }
}

export function exampleSpec(kind: DemoKind, en: boolean): DemoSpec {
  const title = {
    timer: en ? "Focus timer" : "专注计时器",
    tasks: en ? "Project checklist" : "项目清单",
    expenses: en ? "Expense ledger" : "日常账本",
  }[kind];
  return {
    kind, title, description: "", accent: kind === "tasks" ? "rose" : kind === "expenses" ? "amber" : "emerald", minutes: 25,
    items: en ? ["Find a problem worth solving", "Sketch a first version", "Try it with a friend"]
      : ["找到一个想解决的问题", "画出第一版想法", "邀请朋友试用"],
  };
}
