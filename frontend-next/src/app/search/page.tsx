import type { Metadata } from "next";
import { SearchClient } from "@/components/search/search-client";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";
import { parseSearchState } from "@/lib/search-state";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getRequestLocale();
  return {
    title: pickLocaleText(locale, { zh: "搜索", en: "Search" }),
  };
}

type SearchPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolved = await searchParams;
  const params = new URLSearchParams();
  for (const key of ["q", "type", "page"]) {
    if (typeof resolved[key] === "string") params.set(key, resolved[key]);
  }
  const initialState = parseSearchState(params);
  return <SearchClient key={JSON.stringify(initialState)} initialState={initialState} />;
}
