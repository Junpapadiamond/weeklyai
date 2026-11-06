import { tasks as records } from "./records";
import { tasks as operations } from "./operations";
import { tasks as labs } from "./labs";
import { tasks as studios } from "./studios";
import type { Task } from "../types";

export const reviewedTasks: Record<string, Task> = { ...records, ...operations, ...labs, ...studios };
