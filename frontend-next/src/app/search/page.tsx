import { SearchClient } from "@/components/search/search-client";

export const metadata = {
  title: "WeeklyAI - 搜索",
};

type SearchPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolved = await searchParams;
  const query = typeof resolved.q === "string" ? resolved.q : "";

  return <SearchClient initialQuery={query} />;
}
