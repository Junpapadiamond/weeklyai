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
  const copy = {
    timer: en
      ? ["A little room to focus", "One task. A little time. Make room for what matters."]
      : ["留一点时间，专注", "放下其他事情，从眼前的一件小事开始。"],
    tasks: en
      ? ["Make room for good work", "Small steps for your next idea. Check one off and keep going."]
      : ["把想法，变成行动", "把一个大计划拆成小任务，完成一件，就往前一步。"],
    expenses: en
      ? ["The little things add up", "A simple place to keep track of everyday spending."]
      : ["每一笔，都心中有数", "记下日常的小开销，看看今天的钱花在了哪里。"],
  }[kind];
  return {
    kind, title: copy[0], description: copy[1], accent: kind === "tasks" ? "rose" : kind === "expenses" ? "amber" : "emerald", minutes: 25,
    items: en ? ["Find a problem worth solving", "Sketch a first version", "Try it with a friend"]
      : ["找到一个想解决的问题", "画出第一版想法", "邀请朋友试用"],
  };
}
