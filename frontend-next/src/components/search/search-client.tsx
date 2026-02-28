"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { searchProductsClient } from "@/lib/api-client";
import type { SearchParams } from "@/types/api";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ProductCard } from "@/components/product/product-card";

const SEARCH_DEBOUNCE_MS = 360;

type SearchClientProps = {
  initialQuery?: string;
};

export function SearchClient({ initialQuery = "" }: SearchClientProps) {
  const { locale, t } = useSiteLocale();
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
  const statusText = isLoading
    ? t("搜索中...", "Searching...")
    : isValidating
      ? t("更新结果中...", "Updating results...")
      : isDebouncing
        ? t("输入中...", "Typing...")
        : "";
  const errorMessage = error instanceof Error ? error.message : String(error || t("请求失败", "Request failed"));

  return (
    <section className="section search-page">
      <div className="section-header">
        <h1 className="section-title">{t("搜索产品", "Search Products")}</h1>
        <p className="section-desc">{t("仅保留关键词和类型筛选，减少操作负担。", "Keep only keyword and type filters to reduce friction.")}</p>
        <p className="section-micro-note">{t("输入关键词自动搜索，按需切换软件/硬件。", "Type keywords for instant search and switch software/hardware when needed.")}</p>
      </div>

      <form className="search-panel" onSubmit={onSubmit}>
        <input
          type="search"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder={t("输入关键词，例如 agent、硬件、融资...", "Enter keywords, e.g. agent, hardware, funding...")}
          aria-label={t("搜索关键词", "Search keywords")}
          autoComplete="off"
        />
        <div className="search-panel__actions">
          <button type="button" onClick={clearSearch} disabled={!q.trim() && !submittedQ}>
            {t("清空", "Clear")}
          </button>
          <button type="submit">{t("搜索", "Search")}</button>
        </div>
      </form>

      <div className="search-toolbar search-toolbar--minimal">
        <label className="search-toolbar__item">
          {t("类型", "Type")}
          <select value={type} onChange={(event) => updateType(event.target.value as SearchParams["type"])}>
            <option value="all">{t("全部", "All")}</option>
            <option value="software">{t("软件", "Software")}</option>
            <option value="hardware">{t("硬件", "Hardware")}</option>
          </select>
        </label>
        <button
          type="button"
          className="link-btn search-toolbar__reset"
          onClick={resetTypeFilter}
          disabled={!hasTypeFilter}
        >
          {t("重置类型", "Reset type")}
        </button>
      </div>

      {isLoading && !hasResults ? <div className="loading-block">{t("搜索中...", "Searching...")}</div> : null}
      {error ? (
        <div className="error-block">
          {t("搜索失败", "Search failed")}: {errorMessage}
          <button type="button" className="link-btn" onClick={() => mutate()}>
            {t("重试", "Retry")}
          </button>
        </div>
      ) : null}

      {shouldSearch && !error ? (
        <p className="search-result-meta">
          {locale === "en-US"
            ? `${resultCount} results${hasTypeFilter ? ` (${type === "software" ? "Software" : "Hardware"})` : ""}`
            : `共找到 ${resultCount} 个结果${hasTypeFilter ? `（${type === "software" ? "软件" : "硬件"}）` : ""}`}
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
            {t("上一页", "Previous")}
          </button>
          <span>
            {locale === "en-US" ? `Page ${currentPage} / ${totalPages}` : `第 ${currentPage} / ${totalPages} 页`}
          </span>
          <button
            type="button"
            disabled={currentPage >= totalPages || isLoading || isValidating}
            onClick={() => setPage((value) => value + 1)}
          >
            {t("下一页", "Next")}
          </button>
        </div>
      ) : null}

      {!shouldSearch ? (
        <div className="empty-state">
          <p className="empty-state-text">{t("输入关键词开始搜索。", "Enter a keyword to start searching.")}</p>
        </div>
      ) : null}

      {shouldSearch && !isLoading && !isValidating && !error && !hasResults ? (
        <div className="empty-state">
          <p className="empty-state-text">
            {t("没有匹配结果，建议尝试更宽泛关键词或重置筛选。", "No results matched. Try broader keywords or reset filters.")}
          </p>
          <button type="button" className="link-btn" onClick={resetAll}>
            {t("清空并重试", "Clear and retry")}
          </button>
        </div>
      ) : null}
    </section>
  );
}
