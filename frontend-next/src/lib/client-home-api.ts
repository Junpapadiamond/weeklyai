import type { Product } from "@/types/api";
import type { WeeklyTopSort } from "@/lib/api-client";

const DEFAULT_SERVER_BASE = "http://localhost:5000/api/v1";
const INVALID_WEBSITES = new Set(["unknown", "n/a", "na", "none", "null", "undefined", ""]);

function resolveClientApiBase() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envBase) return envBase.replace(/\/$/, "");

  if (typeof window !== "undefined" && window.location.hostname === "localhost") {
    return DEFAULT_SERVER_BASE;
  }

  return "/api/v1";
}

export async function getWeeklyTopClient(limit = 0, sortBy: WeeklyTopSort = "composite"): Promise<Product[]> {
  const base = resolveClientApiBase();
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("sort_by", sortBy);

  const response = await fetch(`${base}/products/weekly-top?${params.toString()}`, {
    headers: { Accept: "application/json" },
  });

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
