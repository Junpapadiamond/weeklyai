import { z } from "zod";
import { DemoSpecSchema, type DemoSpec } from "@/lib/demo-schema";
import { ProductSchema } from "@/lib/schemas";
import { BROWSER_API_BASE, getServerApiBase } from "@/lib/api-base";
import type { Product } from "@/types/api";

/** Why a demo could not be produced. The UI says something different for each. */
export type DemoError =
  | "NOT_GENERATED"
  | "NOT_CONFIGURED"
  | "PROVIDER_UNAVAILABLE"
  | "INVALID_SPEC"
  | "TOO_MANY_REQUESTS"
  | "NOT_FOUND"
  | "UNAVAILABLE";

export type DemoResult =
  | { ok: true; spec: DemoSpec; cached: boolean }
  | { ok: false; error: DemoError; message: string; generationAvailable: boolean };

export type DemoStatus = {
  generationAvailable: boolean;
  liveEndpoints: string[];
  demoCount: number;
  generateLimitPerHour: number;
};

function base(): string {
  return typeof window === "undefined" ? getServerApiBase() : BROWSER_API_BASE;
}

const KNOWN_ERRORS: DemoError[] = [
  "NOT_GENERATED",
  "NOT_CONFIGURED",
  "PROVIDER_UNAVAILABLE",
  "INVALID_SPEC",
  "TOO_MANY_REQUESTS",
  "NOT_FOUND",
];

function toError(payload: unknown): { error: DemoError; message: string; generationAvailable: boolean } {
  const body = (payload ?? {}) as Record<string, unknown>;
  const raw = String(body.error || "");
  return {
    error: (KNOWN_ERRORS as string[]).includes(raw) ? (raw as DemoError) : "UNAVAILABLE",
    message: typeof body.message === "string" ? body.message : "",
    generationAvailable: body.generation_available === true,
  };
}

function parseSpec(payload: unknown): DemoSpec | null {
  const body = (payload ?? {}) as Record<string, unknown>;
  const parsed = DemoSpecSchema.safeParse(body.data);
  return parsed.success ? parsed.data : null;
}

/** Fetch an already-built demo. Never generates. */
export async function fetchDemo(productId: string, signal?: AbortSignal): Promise<DemoResult> {
  try {
    const response = await fetch(`${base()}/demos/${encodeURIComponent(productId)}`, {
      signal: signal || AbortSignal.timeout(12000),
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) return { ok: false, ...toError(payload) };
    const spec = parseSpec(payload);
    if (!spec) {
      return { ok: false, error: "INVALID_SPEC", message: "This demo failed validation and was not rendered.", generationAvailable: false };
    }
    return { ok: true, spec, cached: true };
  } catch {
    return { ok: false, error: "UNAVAILABLE", message: "", generationAvailable: false };
  }
}

/**
 * Build a demo now. Slow by nature — the caller should show elapsed time rather
 * than a fake progress bar, because we genuinely do not know how long it takes.
 */
export async function generateDemo(
  productId: string,
  options: { refresh?: boolean; signal?: AbortSignal } = {}
): Promise<DemoResult> {
  try {
    const response = await fetch(`${base()}/demos/${encodeURIComponent(productId)}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ refresh: options.refresh === true }),
      signal: options.signal || AbortSignal.timeout(75000),
      cache: "no-store",
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) return { ok: false, ...toError(payload) };
    const spec = parseSpec(payload);
    if (!spec) {
      return { ok: false, error: "INVALID_SPEC", message: "The generated demo failed validation.", generationAvailable: true };
    }
    const body = (payload ?? {}) as Record<string, unknown>;
    return { ok: true, spec, cached: body.cached === true };
  } catch {
    return { ok: false, error: "UNAVAILABLE", message: "", generationAvailable: false };
  }
}

export async function fetchDemoStatus(signal?: AbortSignal): Promise<DemoStatus> {
  const fallback: DemoStatus = { generationAvailable: false, liveEndpoints: [], demoCount: 0, generateLimitPerHour: 0 };
  try {
    const response = await fetch(`${base()}/demos/status`, {
      signal: signal || AbortSignal.timeout(8000),
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) return fallback;
    const body = (await response.json()) as Record<string, unknown>;
    return {
      generationAvailable: body.generation_available === true,
      liveEndpoints: Array.isArray(body.live_endpoints) ? body.live_endpoints.map(String) : [],
      demoCount: Number(body.demo_count) || 0,
      generateLimitPerHour: Number(body.generate_limit_per_hour) || 0,
    };
  } catch {
    return fallback;
  }
}

/** Slugs that can be served instantly. Used to mark the picker. */
export async function fetchReadyDemoSlugs(signal?: AbortSignal): Promise<string[]> {
  try {
    const response = await fetch(`${base()}/demos`, {
      signal: signal || AbortSignal.timeout(8000),
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) return [];
    const body = (await response.json()) as Record<string, unknown>;
    return Array.isArray(body.data) ? body.data.map(String) : [];
  } catch {
    return [];
  }
}

/** Must match _slugify in backend/app/services/demo_repository.py. */
export function demoSlug(value: string): string {
  const cleaned = Array.from(String(value || "").trim())
    .map((ch) => (/[a-zA-Z0-9]/.test(ch) ? ch.toLowerCase() : "-"))
    .join("");
  return cleaned.replace(/-+/g, "-").replace(/^-|-$/g, "").slice(0, 120);
}

/** One approved sandbox call. Returns null when live mode is not configured. */
export async function runLiveQuery(endpointId: string, query: string, signal?: AbortSignal): Promise<unknown | null> {
  try {
    const response = await fetch(`${base()}/demos/live`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ endpoint_id: endpointId, query }),
      signal: signal || AbortSignal.timeout(25000),
    });
    if (!response.ok) return null;
    const body = (await response.json()) as Record<string, unknown>;
    return body.success === true ? body.data : null;
  } catch {
    return null;
  }
}

/**
 * Search the whole catalog for the demo picker.
 *
 * The picker's initial grid is only the top of the catalog, so without this a
 * visitor could not reach most products — and "pick any product" is the whole
 * point of the page. Runs against the same search endpoint the site's own
 * search page uses.
 */
export async function searchProductsForDemos(query: string, signal?: AbortSignal): Promise<Product[]> {
  const term = query.trim();
  if (!term) return [];
  try {
    const response = await fetch(`${base()}/search/?q=${encodeURIComponent(term)}&limit=40`, {
      signal: signal || AbortSignal.timeout(12000),
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) return [];
    const body = (await response.json()) as Record<string, unknown>;
    const parsed = z.array(ProductSchema).safeParse(body.data);
    return parsed.success ? parsed.data : [];
  } catch {
    return [];
  }
}
