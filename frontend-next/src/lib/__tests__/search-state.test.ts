import { expect, it } from "vitest";
import { parseSearchState, searchStateUrl } from "../search-state";

it("round-trips Unicode, literal plus, filters and pagination in shared links", () => {
  const state = { q: "智能眼镜 + agent", type: "hardware" as const, page: 3 };
  const url = new URL(searchStateUrl(state), "https://example.test");
  expect(parseSearchState(url.searchParams)).toEqual(state);
});

it.each(["-1", "0", "NaN", "1.5", "1e100"])("normalizes invalid page %s", (page) => {
  expect(parseSearchState(new URLSearchParams({ q: "  agent  ", type: "invalid", page })))
    .toEqual({ q: "agent", type: "all", page: 1 });
});

it("clears all state when the search is reset", () => {
  expect(searchStateUrl({ q: "  ", type: "all", page: 1 })).toBe("/search");
  expect(parseSearchState(new URLSearchParams())).toEqual({ q: "", type: "all", page: 1 });
});
