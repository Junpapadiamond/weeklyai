import { z } from "zod";

const stringOrNumberToNumber = z.union([z.number(), z.string()]).transform((value) => {
  if (typeof value === "number") return value;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
});

export const ProductSchema = z
  .object({
    _id: z.union([z.string(), z.number()]).optional(),
    id: z.union([z.string(), z.number()]).optional(),
    name: z.string().min(1),
    website: z.string().optional(),
    description: z.string().default(""),
    why_matters: z.string().optional(),
    logo_url: z.string().optional(),
    dark_horse_index: stringOrNumberToNumber.optional(),
    category: z.string().optional(),
    categories: z.array(z.string()).optional(),
    hardware_category: z.string().optional(),
    hardware_type: z.string().optional(),
    form_factor: z.string().optional(),
    use_case: z.string().optional(),
    innovation_traits: z.array(z.string()).optional(),
    price: z.string().optional(),
    funding_total: z.string().optional(),
    latest_news: z.string().optional(),
    source: z.string().optional(),
    source_url: z.string().optional(),
    region: z.string().optional(),
    final_score: stringOrNumberToNumber.optional(),
    trending_score: stringOrNumberToNumber.optional(),
    hot_score: stringOrNumberToNumber.optional(),
    weekly_users: stringOrNumberToNumber.optional(),
    first_seen: z.string().optional(),
    published_at: z.string().optional(),
    discovered_at: z.string().optional(),
    is_hardware: z.boolean().optional(),
    needs_verification: z.boolean().optional(),
    extra: z.record(z.string(), z.unknown()).optional(),
  })
  .transform((product) => ({
    ...product,
    _id: product._id !== undefined ? String(product._id) : undefined,
    id: product.id !== undefined ? String(product.id) : undefined,
  }));

export const BlogSchema = z.object({
  name: z.string().min(1),
  description: z.string().default(""),
  website: z.string().optional(),
  logo_url: z.string().optional(),
  source: z.string().optional(),
  published_at: z.string().optional(),
  categories: z.array(z.string()).optional(),
  content_type: z.string().optional(),
  final_score: stringOrNumberToNumber.optional(),
  trending_score: stringOrNumberToNumber.optional(),
  dark_horse_index: stringOrNumberToNumber.optional(),
  extra: z.record(z.string(), z.unknown()).optional(),
});

export const IndustryLeaderProductSchema = z.object({
  name: z.string().min(1),
  company: z.string().optional(),
  website: z.string().optional(),
  logo: z.string().optional(),
  region: z.string().optional(),
  description: z.string().optional(),
  founded: z.string().optional(),
  funding: z.string().optional(),
  valuation: z.string().optional(),
  users: z.string().optional(),
  why_famous: z.string().optional(),
});

export const IndustryLeaderCategorySchema = z.object({
  icon: z.string().optional(),
  description: z.string().optional(),
  products: z.array(IndustryLeaderProductSchema).default([]),
});

export const IndustryLeadersSchema = z.object({
  _meta: z
    .object({
      description: z.string().optional(),
      note: z.string().optional(),
      last_updated: z.string().optional(),
    })
    .optional(),
  categories: z.record(z.string(), IndustryLeaderCategorySchema).default({}),
});

export const LastUpdatedSchema = z.object({
  last_updated: z.string().nullable().optional(),
  hours_ago: stringOrNumberToNumber.nullable().optional(),
});

export const SearchResponseSchema = z.object({
  success: z.boolean().optional(),
  data: z.array(ProductSchema).default([]),
  message: z.string().optional(),
  pagination: z
    .object({
      page: z.number().optional(),
      limit: z.number().optional(),
      total: z.number().optional(),
      pages: z.number().optional(),
    })
    .optional(),
});

export function listEnvelope<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    success: z.boolean().optional(),
    data: z.array(itemSchema).default([]),
    message: z.string().optional(),
  });
}

export function itemEnvelope<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    success: z.boolean().optional(),
    data: itemSchema.nullable().optional(),
    message: z.string().optional(),
  });
}
