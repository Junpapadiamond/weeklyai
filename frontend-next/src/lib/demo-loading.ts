import { readDemo, type DemoResponse, type ExperienceEntry } from "./demo-experience";

const ready = new Map<string, { experience: ExperienceEntry; expires: number }>();
const READ_TIMEOUT = 15000;
// The backend allows 90s for generation plus storage; its proxy allows 110s.
const GENERATION_TIMEOUT = 130000;
const POST_TIMEOUT = 115000;

export async function fetchPreparedDemo(id: string, signal: AbortSignal): Promise<DemoResponse> {
  return readDemo(await fetch(`/api/v1/demos/prepared/${encodeURIComponent(id)}`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(READ_TIMEOUT)]),
  }));
}

function pause(signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const abort = () => { clearTimeout(timer); reject(signal.reason); };
    const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, 2000);
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
  });
}

/** Read-only retries must never reserve another paid generation. */
export async function loadProductDemo(id: string, options: {
  signal: AbortSignal; checkOnly?: boolean; onGenerating?: () => void;
}): Promise<DemoResponse> {
  const cached = ready.get(id);
  if (cached && cached.expires > Date.now()) {
    return { success: true, state: "ready", experience: cached.experience, quota: null, generation_available: false };
  }
  let next = await fetchPreparedDemo(id, options.signal);
  if (!next.success || next.experience) return remember(id, next);
  if (next.state === "generating" || (!options.checkOnly && next.generation_available)) {
    options.onGenerating?.();
    const signal = AbortSignal.any([options.signal, AbortSignal.timeout(GENERATION_TIMEOUT)]);
    if (next.state !== "generating") {
      try {
        next = await readDemo(await fetch("/api/v1/demos/generate", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ product_id: id }),
          signal: AbortSignal.any([signal, AbortSignal.timeout(POST_TIMEOUT)]),
        }));
      } catch (error) {
        if (signal.aborted) throw error;
        if (error instanceof Error && error.message === "GENERATION_INVALID_RESPONSE") throw error;
        next = { ...next, success: false, error: "SERVICE_UNAVAILABLE" };
      }
      // Losing the POST response does not mean generation failed. Recover the
      // saved result or join its lease with GETs only, never a second paid POST.
      if (next.error === "SERVICE_UNAVAILABLE") {
        next = await fetchPreparedDemo(id, signal);
        if (next.success && next.state === "not_generated") {
          return { ...next, success: false, error: "SERVICE_UNAVAILABLE" };
        }
      }
    }
    while (next.success && next.state === "generating" && !next.experience) {
      await pause(signal);
      next = await fetchPreparedDemo(id, signal);
      if (next.success && next.state === "not_generated") {
        return { ...next, success: false, error: "GENERATION_FAILED" };
      }
    }
  }
  return remember(id, next);
}

function remember(id: string, result: DemoResponse): DemoResponse {
  if (result.success && result.experience) {
    if (ready.size >= 50) ready.delete(ready.keys().next().value!);
    ready.set(id, { experience: result.experience, expires: Date.now() + 300000 });
  }
  return result;
}
