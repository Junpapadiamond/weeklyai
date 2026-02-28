import type { BlogPost, Product } from "@/types/api";
import { normalizeDirectionToken, normalizeWebsite, productKey } from "@/lib/product-utils";

export const FAVORITES_KEY = "weeklyai_favorites_v3";
const LEGACY_FAVORITES_KEY = "weeklyai_favorites_v2";
const LEGACY_FAVORITES_KEYS = [LEGACY_FAVORITES_KEY, "weeklyai_favorites"];
export const FAVORITES_EVENT = "weeklyai:favorites";
export const FAVORITES_OPEN_EVENT = "weeklyai:favorites-open";

export type FavoriteKind = "product" | "blog";

export type FavoriteProductEntry = {
  key: string;
  saved_at: string;
  item: Product;
};

export type FavoriteBlogEntry = {
  key: string;
  saved_at: string;
  item: BlogPost;
};

type FavoritesStore = {
  version: 3;
  products: FavoriteProductEntry[];
  blogs: FavoriteBlogEntry[];
};

const EMPTY_STORE: FavoritesStore = {
  version: 3,
  products: [],
  blogs: [],
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function sanitizeProduct(product: Product): Product {
  return {
    _id: product._id,
    id: product.id,
    name: product.name,
    website: product.website,
    description: product.description,
    description_en: product.description_en,
    why_matters: product.why_matters,
    why_matters_en: product.why_matters_en,
    logo_url: product.logo_url,
    logo: product.logo,
    dark_horse_index: product.dark_horse_index,
    category: product.category,
    categories: product.categories,
    hardware_category: product.hardware_category,
    hardware_type: product.hardware_type,
    form_factor: product.form_factor,
    use_case: product.use_case,
    innovation_traits: product.innovation_traits,
    price: product.price,
    funding_total: product.funding_total,
    latest_news: product.latest_news,
    latest_news_en: product.latest_news_en,
    source: product.source,
    source_url: product.source_url,
    region: product.region,
    final_score: product.final_score,
    trending_score: product.trending_score,
    hot_score: product.hot_score,
    weekly_users: product.weekly_users,
    first_seen: product.first_seen,
    published_at: product.published_at,
    discovered_at: product.discovered_at,
    is_hardware: product.is_hardware,
    needs_verification: product.needs_verification,
    extra: product.extra,
  };
}

function sanitizeBlog(blog: BlogPost): BlogPost {
  return {
    name: blog.name,
    description: blog.description,
    website: blog.website,
    logo_url: blog.logo_url,
    logo: blog.logo,
    source: blog.source,
    published_at: blog.published_at,
    categories: blog.categories,
    content_type: blog.content_type,
    final_score: blog.final_score,
    trending_score: blog.trending_score,
    dark_horse_index: blog.dark_horse_index,
    extra: blog.extra,
  };
}

function toProductKey(product: Product): string {
  const key = productKey(product);
  if (key && key !== "::") return key;
  const fallback = String(product._id || product.id || product.name || "")
    .trim()
    .toLowerCase();
  return fallback;
}

function toBlogKey(blog: BlogPost): string {
  const website = normalizeWebsite(blog.website);
  const source = String(blog.source || "unknown")
    .trim()
    .toLowerCase();
  const name = String(blog.name || "")
    .trim()
    .toLowerCase();
  return `${website}::${source}::${name}`;
}

function getLegacyProductCandidates(product: Product): string[] {
  return [product._id, product.id, product.name, toProductKey(product)]
    .map((value) => String(value || "").trim().toLowerCase())
    .filter(Boolean);
}

function normalizeLegacyKey(value: unknown): string {
  return String(value || "").trim().toLowerCase();
}

function readLegacyStore(storageKey: string): unknown[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(storageKey) ?? "";
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function readLegacyFavorites(): string[] {
  if (typeof window === "undefined") return [];

  const deduped = new Set<string>();

  for (const storageKey of LEGACY_FAVORITES_KEYS) {
    const parsed = readLegacyStore(storageKey);
    for (const value of parsed) {
      if (isRecord(value)) {
        for (const candidate of [value.key, value._id, value.id, value.name]) {
          const normalized = normalizeLegacyKey(candidate);
          if (normalized) deduped.add(normalized);
        }
        continue;
      }

      const normalized = normalizeLegacyKey(value);
      if (!normalized) continue;
      deduped.add(normalized);
    }
  }

  return [...deduped];
}

function readLegacyProductEntries(): FavoriteProductEntry[] {
  if (typeof window === "undefined") return [];

  const entries: FavoriteProductEntry[] = [];
  const seen = new Set<string>();

  for (const storageKey of LEGACY_FAVORITES_KEYS) {
    const parsed = readLegacyStore(storageKey);

    for (const value of parsed) {
      if (!isRecord(value)) continue;
      const key = normalizeLegacyKey(value.key || value._id || value.id || value.name);
      if (!key || seen.has(key)) continue;

      const name = String(value.name || key).trim();
      if (!name) continue;

      const categories = Array.isArray(value.categories)
        ? value.categories.map((item) => String(item || "").trim()).filter(Boolean)
        : undefined;
      const saved_at =
        typeof value.saved_at === "string"
          ? value.saved_at
          : typeof value.addedAt === "string"
            ? value.addedAt
            : new Date().toISOString();

      entries.push({
        key,
        saved_at,
        item: sanitizeProduct({
          _id: key,
          id: key,
          name,
          website: typeof value.website === "string" ? value.website : "",
          description: typeof value.description === "string" ? value.description : "",
          logo_url: typeof value.logo_url === "string" ? value.logo_url : undefined,
          logo: typeof value.logo === "string" ? value.logo : undefined,
          categories,
          source: typeof value.source === "string" ? value.source : undefined,
        }),
      });
      seen.add(key);
    }
  }

  return entries;
}

function writeLegacyFavorites(keys: string[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(LEGACY_FAVORITES_KEY, JSON.stringify(keys));
}

function normalizeStore(payload: unknown): FavoritesStore {
  if (!isRecord(payload)) return EMPTY_STORE;

  const products = Array.isArray(payload.products) ? payload.products : [];
  const blogs = Array.isArray(payload.blogs) ? payload.blogs : [];

  const normalizedProducts: FavoriteProductEntry[] = products
    .map((entry) => {
      if (!isRecord(entry) || !isRecord(entry.item)) return null;
      const item = sanitizeProduct(entry.item as Product);
      const key = String(entry.key || toProductKey(item)).trim().toLowerCase();
      if (!key || !item.name) return null;
      return {
        key,
        saved_at: typeof entry.saved_at === "string" ? entry.saved_at : new Date().toISOString(),
        item,
      };
    })
    .filter((entry): entry is FavoriteProductEntry => !!entry);

  const normalizedBlogs: FavoriteBlogEntry[] = blogs
    .map((entry) => {
      if (!isRecord(entry) || !isRecord(entry.item)) return null;
      const item = sanitizeBlog(entry.item as BlogPost);
      const key = String(entry.key || toBlogKey(item)).trim().toLowerCase();
      if (!key || !item.name) return null;
      return {
        key,
        saved_at: typeof entry.saved_at === "string" ? entry.saved_at : new Date().toISOString(),
        item,
      };
    })
    .filter((entry): entry is FavoriteBlogEntry => !!entry);

  return {
    version: 3,
    products: normalizedProducts,
    blogs: normalizedBlogs,
  };
}

export function readFavorites(): FavoritesStore {
  if (typeof window === "undefined") return EMPTY_STORE;
  try {
    const raw = window.localStorage.getItem(FAVORITES_KEY) ?? "";
    if (raw) {
      const parsed = JSON.parse(raw) as unknown;
      const normalized = normalizeStore(parsed);
      if (normalized.products.length || normalized.blogs.length) {
        return normalized;
      }
    }

    // One-time compatibility migration for old frontend favorites payloads.
    const legacyProducts = readLegacyProductEntries();
    if (legacyProducts.length) {
      const migrated: FavoritesStore = {
        version: 3,
        products: legacyProducts,
        blogs: [],
      };
      writeFavorites(migrated);
      return migrated;
    }

    return EMPTY_STORE;
  } catch {
    return EMPTY_STORE;
  }
}

function writeFavorites(store: FavoritesStore) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(FAVORITES_KEY, JSON.stringify(store));
}

export function emitFavoritesChanged() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(FAVORITES_EVENT));
}

function syncLegacyOnAdd(product: Product) {
  const legacy = new Set(readLegacyFavorites());
  const preferred = String(product._id || product.id || product.name || "").trim().toLowerCase();
  if (preferred) {
    legacy.add(preferred);
  }
  writeLegacyFavorites([...legacy]);
}

function syncLegacyOnRemove(product: Product) {
  const candidateSet = new Set(getLegacyProductCandidates(product));
  const next = readLegacyFavorites().filter((item) => !candidateSet.has(item));
  writeLegacyFavorites(next);
}

export function getLegacyOnlyFavoritesCount(store: FavoritesStore = readFavorites()): number {
  const legacy = readLegacyFavorites();
  if (!legacy.length) return 0;

  const covered = new Set<string>();
  for (const entry of store.products) {
    for (const key of getLegacyProductCandidates(entry.item)) {
      covered.add(key);
    }
  }

  return legacy.filter((key) => !covered.has(key)).length;
}

export function countFavorites(): number {
  const store = readFavorites();
  return store.products.length + store.blogs.length + getLegacyOnlyFavoritesCount(store);
}

export function isProductFavorited(product: Product): boolean {
  const key = toProductKey(product);
  if (!key) return false;
  const store = readFavorites();
  if (store.products.some((entry) => entry.key === key)) return true;

  const legacy = readLegacyFavorites();
  if (!legacy.length) return false;
  const candidates = getLegacyProductCandidates(product);
  return candidates.some((candidate) => legacy.includes(candidate));
}

export function isBlogFavorited(blog: BlogPost): boolean {
  const key = toBlogKey(blog);
  if (!key) return false;
  const store = readFavorites();
  return store.blogs.some((entry) => entry.key === key);
}

export function addProductFavorite(product: Product): boolean {
  const key = toProductKey(product);
  if (!key || !product.name) return false;
  const store = readFavorites();
  if (store.products.some((entry) => entry.key === key)) return false;

  const next: FavoritesStore = {
    ...store,
    products: [
      {
        key,
        saved_at: new Date().toISOString(),
        item: sanitizeProduct(product),
      },
      ...store.products,
    ],
  };

  writeFavorites(next);
  syncLegacyOnAdd(product);
  emitFavoritesChanged();
  return true;
}

export function removeProductFavorite(product: Product): boolean {
  const key = toProductKey(product);
  if (!key) return false;
  const store = readFavorites();
  const nextProducts = store.products.filter((entry) => entry.key !== key);
  if (nextProducts.length === store.products.length && !isProductFavorited(product)) return false;

  writeFavorites({
    ...store,
    products: nextProducts,
  });
  syncLegacyOnRemove(product);
  emitFavoritesChanged();
  return true;
}

export function toggleProductFavorite(product: Product): boolean {
  if (isProductFavorited(product)) {
    removeProductFavorite(product);
    return false;
  }
  addProductFavorite(product);
  return true;
}

export function addBlogFavorite(blog: BlogPost): boolean {
  const key = toBlogKey(blog);
  if (!key || !blog.name) return false;
  const store = readFavorites();
  if (store.blogs.some((entry) => entry.key === key)) return false;

  const next: FavoritesStore = {
    ...store,
    blogs: [
      {
        key,
        saved_at: new Date().toISOString(),
        item: sanitizeBlog(blog),
      },
      ...store.blogs,
    ],
  };

  writeFavorites(next);
  emitFavoritesChanged();
  return true;
}

export function removeBlogFavorite(blog: BlogPost): boolean {
  const key = toBlogKey(blog);
  if (!key) return false;
  const store = readFavorites();
  const nextBlogs = store.blogs.filter((entry) => entry.key !== key);
  if (nextBlogs.length === store.blogs.length) return false;

  writeFavorites({
    ...store,
    blogs: nextBlogs,
  });
  emitFavoritesChanged();
  return true;
}

export function toggleBlogFavorite(blog: BlogPost): boolean {
  if (isBlogFavorited(blog)) {
    removeBlogFavorite(blog);
    return false;
  }
  addBlogFavorite(blog);
  return true;
}

export function subscribeFavorites(handler: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }
  window.addEventListener("storage", handler);
  window.addEventListener(FAVORITES_EVENT, handler);
  return () => {
    window.removeEventListener("storage", handler);
    window.removeEventListener(FAVORITES_EVENT, handler);
  };
}

export function openFavoritesPanel(kind: FavoriteKind = "product") {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(FAVORITES_OPEN_EVENT, { detail: { kind } }));
}

export function normalizeBlogFilterToken(value: string): string {
  const normalized = normalizeDirectionToken(value);
  if (!normalized) return "";
  return normalized;
}
