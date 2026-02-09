import type { Product } from "@/types/api";

const DEFAULT_SERVER_BASE = "http://localhost:5000/api/v1";

function resolveClientApiBase() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envBase) return envBase.replace(/\/$/, "");

  if (typeof window !== "undefined" && window.location.hostname === "localhost") {
    return DEFAULT_SERVER_BASE;
  }

  return "/api/v1";
}

export async function getWeeklyTopClient(limit = 0): Promise<Product[]> {
  const base = resolveClientApiBase();
  const response = await fetch(`${base}/products/weekly-top?limit=${limit}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to load products: ${response.status}`);
  }

  const json = (await response.json()) as { data?: unknown };
  if (!Array.isArray(json.data)) {
    return [];
  }

  return json.data as Product[];
}
