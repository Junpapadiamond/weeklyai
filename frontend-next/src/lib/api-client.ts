import { cache } from "react";
import type { ZodType } from "zod";
import { z } from "zod";
import type {
  BlogPost,
  IndustryLeadersPayload,
  LastUpdatedPayload,
  Product,
  SearchParams,
} from "@/types/api";
import { DEFAULT_LOCALE, pickLocaleText, type SiteLocale } from "@/lib/locale";
import {
  BlogSchema,
  IndustryLeadersSchema,
  LastUpdatedSchema,
  ProductSchema,
  SearchResponseSchema,
  itemEnvelope,
  listEnvelope,
} from "@/lib/schemas";

import { BROWSER_API_BASE, getServerApiBase } from "@/lib/api-base";
export type WeeklyTopSort = "composite" | "trending" | "recency" | "funding";
type FetchConfig = RequestInit & { next?: { revalidate?: number; tags?: string[] } };

async function fetchJson(path: string, config?: FetchConfig): Promise<unknown> {
  const base = typeof window === "undefined" ? getServerApiBase() : BROWSER_API_BASE;
  const response = await fetch(`${base}${path}`, {
    ...config,
    signal: config?.signal || AbortSignal.timeout(12000),
    headers: { Accept: "application/json", ...config?.headers },
  });
  if (response.status === 404) return { data: null };
  if (!response.ok) throw new Error(`Product service unavailable (${response.status}). Please retry.`);
  return response.json();
}

function safeParse<T>(schema: ZodType<T>, payload: unknown, fallback: T): T {
  void fallback;
  const result = schema.safeParse(payload);
  if (!result.success) throw new Error("The product service returned invalid data. Please retry.");
  return result.data;
}

const productListSchema = listEnvelope(ProductSchema);
const blogListSchema = listEnvelope(BlogSchema);
const productItemSchema = itemEnvelope(ProductSchema);
const relatedProductsSchema = z.object({ success: z.boolean().optional(), data: z.array(ProductSchema).default([]) });
const leadersEnvelopeSchema = z.object({ success: z.boolean().optional(), data: IndustryLeadersSchema });
const lastUpdatedEnvelopeSchema = z.object({
  success: z.boolean().optional(),
  last_updated: z.string().nullable().optional(),
  hours_ago: z.number().nullable().optional(),
  product_hours_ago: z.number().nullable().optional(),
  message: z.string().optional(),
});
const INVALID_WEBSITE_VALUES = new Set(["unknown", "n/a", "na", "none", "null", "undefined", ""]);

function hasUsableWebsite(product: Product): boolean {
  const website = String(product.website || "")
    .trim()
    .toLowerCase();
  return Boolean(website) && !INVALID_WEBSITE_VALUES.has(website);
}

export const getDarkHorses = cache(async (limit = 10, minIndex = 4): Promise<Product[]> => {
  const json = await fetchJson(`/products/dark-horses?limit=${limit}&min_index=${minIndex}`, {
    cache: "no-store",
  });
  const parsed = safeParse(productListSchema, json, { data: [] });
  return parsed.data.filter(hasUsableWebsite);
});

export const getWeeklyTop = cache(async (limit = 0, sortBy: WeeklyTopSort = "composite"): Promise<Product[]> => {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("sort_by", sortBy);

  const json = await fetchJson(`/products/weekly-top?${params.toString()}`, { cache: "no-store" });
  const parsed = safeParse(productListSchema, json, { data: [] });
  return parsed.data.filter(hasUsableWebsite);
});

export const getIndustryLeaders = cache(async (): Promise<IndustryLeadersPayload> => {
  const json = await fetchJson(`/products/industry-leaders`, {
    next: { revalidate: 3600, tags: ["products", "industry-leaders"] },
  });
  const parsed = safeParse(leadersEnvelopeSchema, json, { data: { categories: {} } });
  return parsed.data;
});

export const getLastUpdated = cache(async (): Promise<LastUpdatedPayload> => {
  const json = await fetchJson(`/products/last-updated`, {
    cache: "no-store",
  });
  const parsed = safeParse(lastUpdatedEnvelopeSchema, json, {});
  return {
    last_updated: parsed.last_updated,
    hours_ago: parsed.product_hours_ago,
  };
});

export async function getBlogs(source = "", limit = 30, market = "hybrid"): Promise<BlogPost[]> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  if (source) params.set("source", source);
  if (market) params.set("market", market);

  const json = await fetchJson(`/products/blogs?${params.toString()}`, {
    next: { revalidate: 120, tags: ["blogs"] },
  });
  const parsed = safeParse(blogListSchema, json, { data: [] });
  return parsed.data;
}

export async function searchProducts(params: SearchParams) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.categories?.length) search.set("categories", params.categories.join(","));
  if (params.type) search.set("type", params.type);
  if (params.sort) search.set("sort", params.sort);
  search.set("page", String(params.page || 1));
  search.set("limit", String(params.limit || 15));

  const json = await fetchJson(`/search/?${search.toString()}`, {
    next: { revalidate: 30, tags: ["search"] },
  });

  return safeParse(SearchResponseSchema, json, {
    data: [],
    pagination: {
      page: params.page || 1,
      limit: params.limit || 15,
      total: 0,
      pages: 0,
    },
  });
}

export const getProductById = cache(async (id: string): Promise<Product | null> => {
  const json = await fetchJson(`/products/${encodeURIComponent(id)}`, {
    next: { revalidate: 120, tags: ["products", `product-${id}`] },
  });
  const parsed = safeParse(productItemSchema, json, { data: null });
  if (!parsed.data) return null;
  return parsed.data;
});

export const getRelatedProducts = cache(async (id: string, limit = 6): Promise<Product[]> => {
  const json = await fetchJson(`/products/${encodeURIComponent(id)}/related?limit=${limit}`, {
    next: { revalidate: 120, tags: ["products", `product-${id}`, "related"] },
  });
  const parsed = safeParse(relatedProductsSchema, json, { data: [] });
  return parsed.data.filter(hasUsableWebsite);
});

export function parseLastUpdatedLabel(hoursAgo: number | null | undefined, locale: SiteLocale = DEFAULT_LOCALE) {
  if (hoursAgo === null || hoursAgo === undefined || Number.isNaN(hoursAgo)) {
    return pickLocaleText(locale, { zh: "数据更新时间未知", en: "Last update time unavailable" });
  }
  if (hoursAgo < 1) {
    return pickLocaleText(locale, { zh: "最新产品记录距今 1 小时内", en: "Newest product record within the last hour" });
  }
  const age = hoursAgo >= 24 ? `${Math.floor(hoursAgo / 24)}${locale === "en-US" ? " days" : " 天"}` : `${Math.floor(hoursAgo)}${locale === "en-US" ? " hours" : " 小时"}`;
  return locale === "en-US" ? `Newest product record: ${age} ago` : `最新产品记录：${age}前`;
}

// Client-side helpers (SWR)
export async function getBlogsClient(source = "", limit = 30, market = "hybrid"): Promise<BlogPost[]> {
  return getBlogs(source, limit, market);
}

export async function searchProductsClient(params: SearchParams) {
  return searchProducts(params);
}

export const LastUpdatedClientSchema = LastUpdatedSchema;
