import Form from "next/form";
import { MagnifyingGlass } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";

export function HomeIntro() {
  const { t } = useSiteLocale();
  return (
    <section className="home-discovery-intro" aria-labelledby="home-heading">
      <h1 id="home-heading">{t("发现 AI 新产品", "Discover AI products")}</h1>
      <Form action="/search" className="home-discovery-search" role="search" aria-label={t("搜索产品", "Search products")}>
        <MagnifyingGlass size={20} aria-hidden="true" />
        <input name="q" type="search" aria-label={t("产品名称或关键词", "Product name or keyword")} placeholder={t("产品名称或用途", "Product or use case")} required maxLength={200} />
        <button type="submit">{t("搜索", "Search")}</button>
      </Form>
    </section>
  );
}
