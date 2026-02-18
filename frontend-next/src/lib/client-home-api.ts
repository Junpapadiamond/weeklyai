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

function canUseLocalPortFallback(base: string) {
  if (process.env.NEXT_PUBLIC_API_BASE_URL) return false;
  return base === DEFAULT_SERVER_BASE;
}

async function requestWeeklyTop(base: string, query: string): Promise<Response> {
  return fetch(`${base}/products/weekly-top?${query}`, {
    headers: { Accept: "application/json" },
  });
}

export async function getWeeklyTopClient(limit = 0, sortBy: WeeklyTopSort = "composite"): Promise<Product[]> {
  const base = resolveClientApiBase();
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("sort_by", sortBy);
  const query = params.toString();

  let response: Response;
  try {
    response = await requestWeeklyTop(base, query);
  } catch (error) {
    if (canUseLocalPortFallback(base)) {
      response = await requestWeeklyTop(LOCAL_FALLBACK_SERVER_BASE, query);
    } else {
      throw error;
    }
  }

  if (!response.ok && canUseLocalPortFallback(base) && [426, 502, 503, 504].includes(response.status)) {
    response = await requestWeeklyTop(LOCAL_FALLBACK_SERVER_BASE, query);
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
