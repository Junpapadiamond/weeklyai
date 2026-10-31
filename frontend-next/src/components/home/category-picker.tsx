"use client";

import { useId, useRef, useState } from "react";
import { CaretDown, Check, MagnifyingGlass } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { filterDirectionOptions } from "@/lib/product-utils";

type CategoryOption = { value: string; label: string; count: number };

export function CategoryPicker({ options, value, onChange }: {
  options: CategoryOption[];
  value: string;
  onChange: (value: string) => void;
}) {
  const { t } = useSiteLocale();
  const id = useId();
  const details = useRef<HTMLDetailsElement>(null);
  const [query, setQuery] = useState("");
  const active = options.find(option => option.value === value);
  const filtered = filterDirectionOptions(options, query);
  const close = (restoreFocus = false) => {
    if (!details.current) return;
    details.current.open = false;
    if (restoreFocus) details.current.querySelector("summary")?.focus();
  };
  const choose = (next: string) => {
    onChange(next);
    close(true);
    setQuery("");
  };
  return (
    <details ref={details} className="home-category-picker"
      onKeyDown={event => { if (event.key === "Escape") { event.preventDefault(); close(true); } }}
      onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) close(); }}
      onToggle={event => { if (event.currentTarget.open) { setQuery(""); event.currentTarget.querySelector("input")?.focus(); } }}>
      <summary aria-controls={id}>
        <span>{active?.label ?? t("全部分类", "All categories")}</span>
        <CaretDown size={16} aria-hidden="true" />
      </summary>
      <div id={id} className="home-category-panel" aria-label={t("产品分类", "Product categories")}>
        <label className="home-category-search">
          <MagnifyingGlass size={18} aria-hidden="true" />
          <input type="search" value={query} onChange={event => setQuery(event.target.value)}
            placeholder={t("搜索分类", "Search categories")} aria-label={t("搜索分类", "Search categories")} autoComplete="off" />
        </label>
        <div className="home-category-options">
          {[{ value: "all", label: t("全部分类", "All categories"), count: 0 }, ...filtered].map(option => (
            <button key={option.value} type="button" aria-pressed={value === option.value}
              onClick={() => choose(option.value)}>
              <span>{option.label}</span>{value === option.value ? <Check size={16} aria-hidden="true" /> : null}
            </button>
          ))}
        </div>
        {filtered.length === 0 && query.trim() ? <p className="home-category-empty">{t("没有匹配的分类", "No matching categories")}</p> : null}
      </div>
    </details>
  );
}
