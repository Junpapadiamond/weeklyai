import type { Metadata } from "next";
import { SearchClient } from "@/components/search/search-client";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getRequestLocale();
  return {
    title: pickLocaleText(locale, { zh: "WeeklyAI - 搜索", en: "WeeklyAI - Search" }),
  };
}

type SearchPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolved = await searchParams;
  const query = typeof resolved.q === "string" ? resolved.q : "";

  return <SearchClient initialQuery={query} />;
}
