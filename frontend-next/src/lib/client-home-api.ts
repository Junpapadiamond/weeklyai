import type { Product } from "@/types/api";
import type { WeeklyTopSort } from "@/lib/api-client";

const DEFAULT_SERVER_BASE = "http://localhost:5000/api/v1";
const LOCAL_FALLBACK_SERVER_BASE = "http://localhost:5001/api/v1";
const INVALID_WEBSITES = new Set(["unknown", "n/a", "na", "none", "null", "undefined", ""]);

function resolveClientApiBase() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envBase) return envBase.replace(/\/$/, "");

  if (typeof window !== "undefined" && window.location.hostname === "localhost") {
    return DEFAULT_SERVER_BASE;
  }

  return "/api/v1";
}

function resolveLocalFallbackBase(base: string): string | null {
  try {
    const parsed = new URL(base);
    const host = parsed.hostname.toLowerCase();
    const isLocalHost = host === "localhost" || host === "127.0.0.1" || host === "::1";
    const normalizedPort = parsed.port || (parsed.protocol === "https:" ? "443" : "80");
    if (!isLocalHost || normalizedPort !== "5000") return null;
    parsed.port = "5001";
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return base === DEFAULT_SERVER_BASE ? LOCAL_FALLBACK_SERVER_BASE : null;
  }
}

async function requestWeeklyTop(base: string, query: string): Promise<Response> {
  return fetch(`${base}/products/weekly-top?${query}`, {
    headers: { Accept: "application/json" },
  });
}

export async function getWeeklyTopClient(limit = 0, sortBy: WeeklyTopSort = "composite"): Promise<Product[]> {
  const base = resolveClientApiBase();
  const fallbackBase = resolveLocalFallbackBase(base);
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("sort_by", sortBy);
  const query = params.toString();

  let response: Response;
  try {
    response = await requestWeeklyTop(base, query);
  } catch (error) {
    if (fallbackBase) {
      response = await requestWeeklyTop(fallbackBase, query);
    } else {
      throw error;
    }
  }

  if (!response.ok && fallbackBase && [426, 502, 503, 504].includes(response.status)) {
    response = await requestWeeklyTop(fallbackBase, query);
  }

  if (!response.ok) {
    throw new Error(`Failed to load products: ${response.status}`);
  }

  const json = (await response.json()) as { data?: unknown };
  if (!Array.isArray(json.data)) {
    return [];
  }

  return (json.data as Product[]).filter((product) => {
    const website = String(product.website || "")
      .trim()
      .toLowerCase();
    return !INVALID_WEBSITES.has(website);
  });
}
