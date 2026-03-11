import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BlogPost, Product } from "@/types/api";
import {
  addBlogFavorite,
  addProductFavorite,
  clearFavorites,
  countFavorites,
  exportFavorites,
  FAVORITES_EVENT,
  readFavorites,
  subscribeFavorites,
} from "@/lib/favorites";

class MemoryStorage {
  private readonly store = new Map<string, string>();

  clear() {
    this.store.clear();
  }

  getItem(key: string) {
    return this.store.get(key) ?? null;
  }

  setItem(key: string, value: string) {
    this.store.set(key, value);
  }

  removeItem(key: string) {
    this.store.delete(key);
  }
}

type Listener = (event: Event) => void;

function createWindowMock() {
  const storage = new MemoryStorage();
  const listeners = new Map<string, Set<Listener>>();

  return {
    localStorage: storage,
    addEventListener(type: string, handler: Listener) {
      const bucket = listeners.get(type) || new Set<Listener>();
      bucket.add(handler);
      listeners.set(type, bucket);
    },
    removeEventListener(type: string, handler: Listener) {
      listeners.get(type)?.delete(handler);
    },
    dispatchEvent(event: Event) {
      listeners.get(event.type)?.forEach((handler) => handler(event));
      return true;
    },
  };
}

describe("favorites helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("window", createWindowMock());
  });

  it("exports favorites for the active kind", () => {
    const product: Product = {
      name: "Signal",
      description: "Promising AI startup",
      website: "https://signal.example",
      dark_horse_index: 4,
    };

    addProductFavorite(product);
    const exported = JSON.parse(exportFavorites("product")) as {
      kind: string;
      products: Array<{ item: Product }>;
      blogs: BlogPost[];
    };

    expect(exported.kind).toBe("product");
    expect(exported.products).toHaveLength(1);
    expect(exported.products[0]?.item.name).toBe("Signal");
    expect(exported.blogs).toEqual([]);
  });

  it("clears product and blog favorites independently", () => {
    addProductFavorite({
      name: "Signal",
      description: "Promising AI startup",
      website: "https://signal.example",
      dark_horse_index: 4,
    });

    addBlogFavorite({
      name: "Signal News",
      description: "Funding round update",
      website: "https://news.example",
      source: "tech_news",
    });

    expect(countFavorites()).toBe(2);
    expect(clearFavorites("product")).toBe(true);
    expect(readFavorites().products).toHaveLength(0);
    expect(readFavorites().blogs).toHaveLength(1);

    expect(clearFavorites("blog")).toBe(true);
    expect(readFavorites().blogs).toHaveLength(0);
  });

  it("emits favorite change events through subscribeFavorites listeners", () => {
    const handler = vi.fn();
    const unsubscribe = subscribeFavorites(handler);

    window.dispatchEvent(new Event(FAVORITES_EVENT));
    expect(handler).toHaveBeenCalledTimes(1);

    unsubscribe();
  });
});
