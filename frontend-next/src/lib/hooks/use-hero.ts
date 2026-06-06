"use client";

import useSWR from "swr";
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

const fetcher = async (url: string): Promise<Product | null> => {
  const response = await fetch(`${resolveClientApiBase()}${url}`, { headers: { Accept: "application/json" } });
  if (!response.ok) return null;
  const json = (await response.json()) as { data?: Product | null };
  return json.data || null;
};

export function useHero() {
  return useSWR<Product | null>("/products/hero", fetcher);
}
