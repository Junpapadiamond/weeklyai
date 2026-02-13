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
import {
  BlogSchema,
  IndustryLeadersSchema,
  LastUpdatedSchema,
  ProductSchema,
  SearchResponseSchema,
  itemEnvelope,
  listEnvelope,
} from "@/lib/schemas";

const DEFAULT_SERVER_BASE = "http://localhost:5000/api/v1";

function resolveApiBaseUrl() {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_SERVER_BASE;
  }
  return process.env.API_BASE_URL_SERVER || process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_SERVER_BASE;
}

type FetchConfig = RequestInit & {
  next?: {
    revalidate?: number;
    tags?: string[];
  };
};

async function fetchJson(path: string, config?: FetchConfig): Promise<unknown> {
  const baseUrl = resolveApiBaseUrl().replace(/\/$/, "");
  const url = `${baseUrl}${path}`;
  try {
    const response = await fetch(url, {
      ...config,
      headers: {
        Accept: "application/json",
        ...(config?.headers || {}),
      },
    });

    if (!response.ok) {
      if (typeof window !== "undefined") {
        throw new Error(`API request failed: ${response.status} ${response.statusText} (${url})`);
      }
      console.warn(`API request failed: ${response.status} ${response.statusText} (${url})`);
      return {};
    }

    return response.json();
  } catch (error) {
    if (typeof window !== "undefined") {
      throw error;
    }
    console.warn(`API request error (${url})`, error);
    return {};
  }
}

function safeParse<T>(schema: ZodType<T>, payload: unknown, fallback: T): T {
  const result = schema.safeParse(payload);
  if (!result.success) {
    console.warn("API schema mismatch", result.error.format());
    return fallback;
  }
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
    next: { revalidate: 120, tags: ["products", "dark-horses"] },
  });
  const parsed = safeParse(productListSchema, json, { data: [] });
  return parsed.data.filter(hasUsableWebsite);
});

export const getWeeklyTop = cache(async (limit = 0): Promise<Product[]> => {
  const json = await fetchJson(`/products/weekly-top?limit=${limit}`, {
    next: { revalidate: 120, tags: ["products", "weekly-top"] },
  });
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
    next: { revalidate: 60, tags: ["products", "last-updated"] },
  });
  const parsed = safeParse(lastUpdatedEnvelopeSchema, json, {});
  return {
    last_updated: parsed.last_updated,
    hours_ago: parsed.hours_ago,
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
  return hasUsableWebsite(parsed.data) ? parsed.data : null;
});

export const getRelatedProducts = cache(async (id: string, limit = 6): Promise<Product[]> => {
  const json = await fetchJson(`/products/${encodeURIComponent(id)}/related?limit=${limit}`, {
    next: { revalidate: 120, tags: ["products", `product-${id}`, "related"] },
  });
  const parsed = safeParse(relatedProductsSchema, json, { data: [] });
  return parsed.data.filter(hasUsableWebsite);
});

export function parseLastUpdatedLabel(hoursAgo: number | null | undefined) {
  if (hoursAgo === null || hoursAgo === undefined || Number.isNaN(hoursAgo)) {
    return "📡 数据更新时间未知";
  }
  if (hoursAgo < 1) {
    return "📡 数据更新于 1 小时内";
  }
  return `📡 数据更新于 ${hoursAgo.toFixed(1)} 小时前`;
}

// Client-side helpers (SWR)
export async function getBlogsClient(source = "", limit = 30, market = "hybrid"): Promise<BlogPost[]> {
  return getBlogs(source, limit, market);
}

export async function searchProductsClient(params: SearchParams) {
  return searchProducts(params);
}

export const LastUpdatedClientSchema = LastUpdatedSchema;
