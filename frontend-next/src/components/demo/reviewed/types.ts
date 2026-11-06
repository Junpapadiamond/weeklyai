export type Copy = [zh: string, en: string];
type Triple = [Copy, Copy, Copy];
type Pair = [number, number];
type FilterAxis = [Copy, "min" | "max", number];

type Activity =
  | { kind: "evidence"; rows: Triple[] }
  | { kind: "quiz"; rows: Triple[] }
  | { kind: "search"; rows: Triple[]; query: Copy }
  | { kind: "threshold"; axes: FilterAxis[]; rows: [Copy, number, number][] }
  | { kind: "policy"; rules: Copy[]; rows: [Copy, number[]][] }
  | { kind: "slots"; times: Copy[]; rows: [Copy, number[]][] }
  | { kind: "routing"; queues: Copy[]; rows: [Copy, Copy, number][] }
  | { kind: "budget"; unit: Copy; capacity: number; rows: [Copy, number][] }
  | { kind: "ledger"; unit: Copy; rows: [Copy, Copy, number][] }
  | { kind: "path"; target: Copy; obstacle: Copy; goal: number; walls: number[] }
  | { kind: "learning"; axis: Copy; classes: Copy[]; train: Pair[]; tests: Pair[] }
  | { kind: "patch"; variant: "retry" | "stock" | "cents"; original: Copy; fix: Copy; tests: Pair[] }
  | { kind: "slides" | "diagram" | "logic" | "advance" | "mix" | "cache" | "builder"
      | "inertial" | "camera" | "redundancy" | "replay" | "rollout" | "damage" };

export type Task = Activity & { title: Copy; instruction: Copy; result: Copy; source: string; concept?: boolean };
export type TaskOf<K extends Activity["kind"]> = Task & { kind: K };
export type Lang = 0 | 1;
export type Props<K extends Activity["kind"]> = { task: TaskOf<K>; lang: Lang };
