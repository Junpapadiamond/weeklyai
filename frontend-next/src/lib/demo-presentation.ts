import { availableExperienceOptions, type Experience, type ExperienceArtifactData } from "./demo-experience";

type Choices = Record<string, string>;
type ExperienceStep = Experience["steps"][number];
type ExperienceOption = ExperienceStep["options"][number];

/** A prepared path, resolved in dependency order. These are not completed user actions. */
export function defaultExperienceChoices(spec: Experience): Choices {
  const choices: Choices = {};
  for (const step of spec.steps) {
    const first = availableExperienceOptions(step, choices)[0];
    if (first) choices[step.id] = first.id;
  }
  return choices;
}

/** Keep independent edits; reset affected branches, including transitive dependencies. */
export function selectExperienceChoice(spec: Experience, choices: Choices, stepId: string, optionId: string): Choices {
  const target = spec.steps.find(step => step.id === stepId);
  if (!target || !availableExperienceOptions(target, choices).some(option => option.id === optionId)) return choices;
  const next: Choices = {};
  const changed = new Set<string>();
  for (const step of spec.steps) {
    const options = availableExperienceOptions(step, next);
    const dependencyChanged = step.options.some(option => option.when && changed.has(option.when.step_id));
    const wanted = step.id === stepId ? optionId : dependencyChanged ? undefined : choices[step.id];
    const selected = options.find(option => option.id === wanted) ?? options[0];
    if (selected) next[step.id] = selected.id;
    if (dependencyChanged || next[step.id] !== choices[step.id]) changed.add(step.id);
  }
  return Object.keys(next).length === Object.keys(choices).length && Object.entries(next).every(([id, choice]) => choices[id] === choice)
    ? choices : next;
}

export function initialExperienceIndex(spec: Experience): number {
  const explicit = spec.steps.findIndex(step => step.id === spec.focus_step_id);
  if (explicit >= 0) return explicit;
  const artifact = spec.steps.findIndex(step => step.widget === "app" || step.options.some(option => option.artifact));
  return Math.max(0, artifact);
}

/** Legacy output remains whole. Layout changes must not rewrite or regenerate cached content. */
export function experienceArtifact(_spec: Experience, _step: ExperienceStep, selected?: ExperienceOption): ExperienceArtifactData {
  if (selected?.artifact) return selected.artifact;
  return {
    kind: "text",
    input_label: { zh: "示例选择", en: "Example choice" },
    output_label: { zh: "预先准备的示例", en: "Prepared example" },
    input: selected?.label ?? { zh: "请选择一个示例", en: "Choose an example" },
    output: selected?.output ?? { zh: "选择一项后，在这里查看预先准备的结果。", en: "Choose an option to inspect its prepared result here." },
  };
}

/** Literal matching only: no regex, markup parsing, or generated HTML. */
export function artifactInputParts(text: string, emphasis?: string): { text: string; emphasized: boolean }[] {
  if (!emphasis) return [{ text, emphasized: false }];
  const index = text.indexOf(emphasis);
  if (index < 0) return [{ text, emphasized: false }];
  return [
    { text: text.slice(0, index), emphasized: false },
    { text: emphasis, emphasized: true },
    { text: text.slice(index + emphasis.length), emphasized: false },
  ].filter(part => part.text.length > 0);
}
