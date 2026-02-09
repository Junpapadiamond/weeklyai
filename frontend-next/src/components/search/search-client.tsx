"use client";

import { FormEvent, useMemo, useState } from "react";
import useSWR from "swr";
import { searchProductsClient } from "@/lib/api-client";
import type { SearchParams } from "@/types/api";
import { ProductCard } from "@/components/product/product-card";

const CATEGORY_OPTIONS = [
  "coding",
  "image",
  "video",
  "voice",
  "writing",
  "hardware",
  "finance",
  "education",
  "healthcare",
  "agent",
  "other",
];
const QUICK_QUERIES = ["ai agent", "ai hardware", "融资", "开源", "视频生成", "开发工具"];

type SearchClientProps = {
  initialQuery?: string;
};

export function SearchClient({ initialQuery = "" }: SearchClientProps) {
  const [q, setQ] = useState(initialQuery);
  const [submittedQ, setSubmittedQ] = useState(initialQuery);
  const [type, setType] = useState<SearchParams["type"]>("all");
  const [sort, setSort] = useState<SearchParams["sort"]>("trending");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [page, setPage] = useState(1);

  const params = useMemo<SearchParams>(
    () => ({
      q: submittedQ,
      categories: selectedCategories,
      type,
      sort,
      page,
      limit: 20,
    }),
    [page, selectedCategories, sort, submittedQ, type]
  );

  const shouldSearch = submittedQ.trim().length > 0;

  const { data, isLoading, error } = useSWR(
    shouldSearch ? ["search", params] : null,
    ([, payload]) => searchProductsClient(payload),
    { dedupingInterval: 20_000, revalidateOnFocus: false }
  );

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setSubmittedQ(q.trim());
  }

  function clearFilters() {
    setType("all");
    setSort("trending");
    setSelectedCategories([]);
    setPage(1);
  }

  function applyQuickQuery(keyword: string) {
    setQ(keyword);
    setSubmittedQ(keyword);
    setPage(1);
  }

  function toggleCategory(category: string) {
    setPage(1);
    setSelectedCategories((current) => {
      if (current.includes(category)) return current.filter((item) => item !== category);
      return [...current, category];
    });
  }

  const resultCount = data?.pagination?.total ?? 0;

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">搜索产品</h1>
        <p className="section-desc">支持关键词、分类、类型、排序组合搜索</p>
        <p className="section-micro-note">先用关键词粗筛，再用类型/分类收窄候选。</p>
      </div>

      <div className="quick-query-row" aria-label="快捷搜索">
        {QUICK_QUERIES.map((keyword) => (
          <button key={keyword} type="button" className="tag-btn quick-query-btn" onClick={() => applyQuickQuery(keyword)}>
            {keyword}
          </button>
        ))}
      </div>

      <form className="search-panel" onSubmit={onSubmit}>
        <input
          type="search"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder="输入关键词，例如 agent、硬件、融资..."
          aria-label="搜索关键词"
        />
        <button type="submit">搜索</button>
      </form>

      <div className="search-toolbar">
        <label>
          类型
          <select value={type} onChange={(event) => setType(event.target.value as SearchParams["type"])}>
            <option value="all">全部</option>
            <option value="software">软件</option>
            <option value="hardware">硬件</option>
          </select>
        </label>

        <label>
          排序
          <select value={sort} onChange={(event) => setSort(event.target.value as SearchParams["sort"])}>
            <option value="trending">热度</option>
            <option value="rating">评分</option>
            <option value="users">用户数</option>
          </select>
        </label>
      </div>

      <div className="tag-grid">
        {CATEGORY_OPTIONS.map((category) => {
          const active = selectedCategories.includes(category);
          return (
            <button
              key={category}
              type="button"
              className={`tag-btn ${active ? "active" : ""}`}
              onClick={() => toggleCategory(category)}
            >
              {category}
            </button>
          );
        })}
      </div>

      <div className="active-filter-strip">
        <span className="active-filter-chip">类型: {type}</span>
        <span className="active-filter-chip">排序: {sort}</span>
        <span className="active-filter-chip">分类数: {selectedCategories.length}</span>
        <button type="button" className="link-btn" onClick={clearFilters}>
          清空筛选
        </button>
      </div>

      {isLoading ? <div className="loading-block">搜索中...</div> : null}
      {error ? <div className="error-block">搜索失败: {String(error)}</div> : null}

      {shouldSearch && !isLoading && !error ? (
        <p className="search-result-meta">共找到 {resultCount} 个结果</p>
      ) : null}

      <div className="products-grid">
        {data?.data.map((product) => (
          <ProductCard key={product._id || product.name} product={product} />
        ))}
      </div>

      {data?.pagination && data.pagination.pages && data.pagination.pages > 1 ? (
        <div className="pagination">
          <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
            上一页
          </button>
          <span>
            第 {page} / {data.pagination.pages} 页
          </span>
          <button
            type="button"
            disabled={page >= data.pagination.pages}
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

      {shouldSearch && !isLoading && !error && data?.data.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-text">没有匹配结果，建议尝试更宽泛关键词。</p>
        </div>
      ) : null}
    </section>
  );
}
