import type { HookType } from "@/types/api";

export const HOOK_COLORS: Record<HookType, string> = {
  weird_form: "#396f4f",
  new_behavior: "#b9522d",
  unexpected_combo: "#8f4f8a",
  quiet_real_problem: "#496575",
  new_interaction: "#9a7a19",
  niche_depth: "#5f5399",
};

export const HOOK_LABELS_ZH: Record<HookType, string> = {
  weird_form: "形态奇特",
  new_behavior: "新行为",
  unexpected_combo: "意外组合",
  quiet_real_problem: "真实痛点",
  new_interaction: "新交互",
  niche_depth: "垂直深挖",
};

export const HOOK_LABELS_EN: Record<HookType, string> = {
  weird_form: "Weird form",
  new_behavior: "New behavior",
  unexpected_combo: "Unexpected combo",
  quiet_real_problem: "Real problem",
  new_interaction: "New interaction",
  niche_depth: "Niche depth",
};

export function resolveHook(value: string | undefined | null): HookType {
  if (
    value === "weird_form" ||
    value === "new_behavior" ||
    value === "unexpected_combo" ||
    value === "quiet_real_problem" ||
    value === "new_interaction" ||
    value === "niche_depth"
  ) {
    return value;
  }
  return "quiet_real_problem";
}
