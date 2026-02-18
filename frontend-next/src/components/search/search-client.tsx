"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { searchProductsClient } from "@/lib/api-client";
import type { SearchParams } from "@/types/api";
import { ProductCard } from "@/components/product/product-card";

const SEARCH_DEBOUNCE_MS = 360;

type SearchClientProps = {
  initialQuery?: string;
};

export function SearchClient({ initialQuery = "" }: SearchClientProps) {
  const seedQuery = initialQuery.trim();
  const [q, setQ] = useState(seedQuery);
  const [submittedQ, setSubmittedQ] = useState(seedQuery);
  const [type, setType] = useState<SearchParams["type"]>("all");
  const [page, setPage] = useState(1);

  const params = useMemo<SearchParams>(
    () => ({
      q: submittedQ,
      categories: [],
      type,
      sort: "trending",
      page,
      limit: 20,
    }),
    [page, submittedQ, type]
  );

  const shouldSearch = submittedQ.trim().length > 0;
  const isDebouncing = q.trim() !== submittedQ;

  const { data, isLoading, isValidating, error, mutate } = useSWR(
    shouldSearch ? ["search", params] : null,
    ([, payload]) => searchProductsClient(payload),
    { dedupingInterval: 20_000, revalidateOnFocus: false, keepPreviousData: true }
  );

  useEffect(() => {
    const next = q.trim();
    if (next === submittedQ) {
      return;
    }

    const timer = window.setTimeout(() => {
      setPage(1);
      setSubmittedQ(next);
    }, SEARCH_DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
  }, [q, submittedQ]);

  function commitQuery(nextValue: string) {
    const normalized = nextValue.trim();
    setPage(1);
    setSubmittedQ(normalized);
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    commitQuery(q);
  }

  function resetTypeFilter() {
    setType("all");
    setPage(1);
  }

  function clearSearch() {
    setQ("");
    commitQuery("");
  }

  function resetAll() {
    setQ("");
    setSubmittedQ("");
    setType("all");
    setPage(1);
  }

  function updateType(nextType: SearchParams["type"]) {
    setType(nextType);
    setPage(1);
  }

  const resultCount = data?.pagination?.total ?? 0;
  const totalPages = data?.pagination?.pages ?? 0;
  const currentPage = data?.pagination?.page ?? page;
  const hasResults = (data?.data.length ?? 0) > 0;
  const hasTypeFilter = type !== "all";
  const statusText = isLoading ? "搜索中..." : isValidating ? "更新结果中..." : isDebouncing ? "输入中..." : "";
  const errorMessage = error instanceof Error ? error.message : String(error || "请求失败");

  return (
    <section className="section search-page">
      <div className="section-header">
        <h1 className="section-title">搜索产品</h1>
        <p className="section-desc">仅保留关键词和类型筛选，减少操作负担。</p>
        <p className="section-micro-note">输入关键词自动搜索，按需切换软件/硬件。</p>
      </div>

      <form className="search-panel" onSubmit={onSubmit}>
        <input
          type="search"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder="输入关键词，例如 agent、硬件、融资..."
          aria-label="搜索关键词"
          autoComplete="off"
        />
        <div className="search-panel__actions">
          <button type="button" onClick={clearSearch} disabled={!q.trim() && !submittedQ}>
            清空
          </button>
          <button type="submit">搜索</button>
        </div>
      </form>

      <div className="search-toolbar search-toolbar--minimal">
        <label className="search-toolbar__item">
          类型
          <select value={type} onChange={(event) => updateType(event.target.value as SearchParams["type"])}>
            <option value="all">全部</option>
            <option value="software">软件</option>
            <option value="hardware">硬件</option>
          </select>
        </label>
        <button
          type="button"
          className="link-btn search-toolbar__reset"
          onClick={resetTypeFilter}
          disabled={!hasTypeFilter}
        >
          重置类型
        </button>
      </div>

      {isLoading && !hasResults ? <div className="loading-block">搜索中...</div> : null}
      {error ? (
        <div className="error-block">
          搜索失败: {errorMessage}
          <button type="button" className="link-btn" onClick={() => mutate()}>
            重试
          </button>
        </div>
      ) : null}

      {shouldSearch && !error ? (
        <p className="search-result-meta">
          共找到 {resultCount} 个结果{hasTypeFilter ? `（${type === "software" ? "软件" : "硬件"}）` : ""}
          {statusText ? ` · ${statusText}` : ""}
        </p>
      ) : null}

      {hasResults ? (
        <div className="products-grid search-results-grid">
          {data?.data.map((product) => (
            <ProductCard key={product._id || product.name} product={product} />
          ))}
        </div>
      ) : null}

      {data?.pagination && totalPages > 1 ? (
        <div className="pagination">
          <button
            type="button"
            disabled={currentPage <= 1 || isLoading || isValidating}
            onClick={() => setPage((value) => Math.max(1, value - 1))}
          >
            上一页
          </button>
          <span>
            第 {currentPage} / {totalPages} 页
          </span>
          <button
            type="button"
            disabled={currentPage >= totalPages || isLoading || isValidating}
            onClick={() => setPage((value) => value + 1)}
          >
            下一页
          </button>
        </div>
      ) : null}

      {!shouldSearch ? (
        <div className="empty-state">
          <p className="empty-state-text">输入关键词开始搜索。</p>
        </div>
      ) : null}

      {shouldSearch && !isLoading && !isValidating && !error && !hasResults ? (
        <div className="empty-state">
          <p className="empty-state-text">没有匹配结果，建议尝试更宽泛关键词或重置筛选。</p>
          <button type="button" className="link-btn" onClick={resetAll}>
            清空并重试
          </button>
        </div>
      ) : null}
    </section>
  );
}
