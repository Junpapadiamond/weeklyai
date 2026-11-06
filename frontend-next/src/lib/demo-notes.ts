import type { ExperienceArtifactData } from "./demo-experience";

export type ItemDraft = { order?: number[]; picked?: number[] };
export type ArtifactItemsData = NonNullable<ExperienceArtifactData["items"]>;

export function itemNotes(items: ArtifactItemsData, indices: number[], lang: "en" | "zh") {
  return indices.map((index, position) => `${position + 1}. ${items[index].label[lang]}\n${items[index].detail[lang]}`);
}

export function downloadDemoText(lines: string[], filename: string) {
  const url = URL.createObjectURL(new Blob([lines.filter(Boolean).join("\n\n")], { type: "text/plain;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
