import Form from "next/form";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, ArrowUpRight, MagnifyingGlass } from "@phosphor-icons/react";
import { RadarEmblem } from "@/components/brand/radar-emblem";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { fetchPreparedDemo } from "@/lib/demo-loading";
import { handleExternalAnchorClick } from "@/lib/external-navigation";
import { supportsLiveDemo } from "@/lib/live-demo";
import {
  cleanDescription, getLocalizedProductDescription, getProductScore, isValidWebsite,
  resolveProductLogoSources,
} from "@/lib/product-utils";
import type { Product } from "@/types/api";

function Spotlight({ product }: { product: Product }) {
  const { locale, t } = useSiteLocale();
  const id = product._id || product.id || product.name;
  const detailUrl = `/product/${encodeURIComponent(id)}`;
  const eligible = !product.needs_verification && supportsLiveDemo(product);
  const [ready, setReady] = useState(false);
  const score = getProductScore(product);
  const recordedDate = (product.discovered_at || product.first_seen || "").slice(0, 10);
  const summary = cleanDescription(getLocalizedProductDescription(product, locale), locale);
  const source = product.source_url && isValidWebsite(product.source_url) ? product.source_url : null;

  useEffect(() => {
    if (!eligible) return;
    const controller = new AbortController();
    fetchPreparedDemo(String(id), controller.signal).then(response => {
      if (!controller.signal.aborted) setReady(Boolean(response.success && response.experience));
    }).catch(() => { /* The catalog record remains usable when playback is unavailable. */ });
    return () => controller.abort();
  }, [eligible, id]);

  return <article className="home-spotlight">
    <div className="home-spotlight__identity">
      <SmartLogo className="home-spotlight__logo" name={product.name} {...resolveProductLogoSources(product)}
        website={product.website} sourceUrl={product.source_url} trustPrimaryLogo size={46} loading="eager" />
      <h2 className="home-spotlight__name"><Link href={detailUrl}>{product.name}</Link></h2>
    </div>
    {summary ? <p className="home-spotlight__summary">{summary}</p> : null}
    <div className="home-spotlight__actions">
      <Link href={detailUrl} className="home-spotlight__action">{t("了解产品", "View details")} <ArrowRight size={16} /></Link>
      {eligible && ready ? <Link href={detailUrl + "#try-demo"} className="home-spotlight__example">{t("体验示例", "Try example")}</Link> : null}
    </div>
    <div className="home-spotlight__record">
      {score > 0 ? <span>{t("黑马指数", "Discovery score")} {score}/5</span> : null}
      {recordedDate ? <time dateTime={recordedDate}>{recordedDate}</time> : null}
      {source ? <a href={source} target="_blank" rel="noopener noreferrer" onClick={event => handleExternalAnchorClick(event, source)}>{t("来源", "Source")} <ArrowUpRight size={13} /></a> : null}
      <FavoriteButton product={product} showLabel />
    </div>
  </article>;
}

export function HomeIntro({ product, archived }: { product?: Product; archived: boolean }) {
  const { t } = useSiteLocale();
  return (
    <section className="home-discovery-intro" aria-labelledby="home-heading">
      <div className="home-hero__story">
        <h1 id="home-heading">{archived ? t("往期 AI 黑马", "From the AI product archive") : t("发现崭露头角的 AI 产品", "Discover emerging AI products")}</h1>
        {product ? <Spotlight key={product._id || product.id || product.name} product={product} /> : null}
      </div>
      <RadarEmblem animated pauseLabel={t("暂停雷达动画", "Pause radar animation")} resumeLabel={t("继续雷达动画", "Resume radar animation")} />
      <Form action="/search" className="home-discovery-search" role="search" aria-label={t("搜索产品", "Search products")}>
        <MagnifyingGlass size={19} aria-hidden="true" />
        <input name="q" type="search" aria-label={t("产品名称或关键词", "Product name or keyword")} placeholder={t("产品名称或用途", "Name or use case")} required maxLength={200} />
        <button type="submit">{t("搜索", "Search")}</button>
      </Form>
    </section>
  );
}
