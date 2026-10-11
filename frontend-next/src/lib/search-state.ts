export type SearchState = { q: string; type: "all" | "software" | "hardware"; page: number };

export function parseSearchState(params: URLSearchParams): SearchState {
  const type = params.get("type");
  const page = Number(params.get("page"));
  return {
    q: (params.get("q") || "").trim(),
    type: type === "hardware" || type === "software" ? type : "all",
    page: Number.isSafeInteger(page) && page > 0 ? page : 1,
  };
}

export function searchStateUrl(state: SearchState): string {
  const params = new URLSearchParams();
  if (state.q.trim()) params.set("q", state.q.trim());
  if (state.type !== "all") params.set("type", state.type);
  if (state.page > 1) params.set("page", String(state.page));
  return `/search${params.size ? `?${params}` : ""}`;
}
