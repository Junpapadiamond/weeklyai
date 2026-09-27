"use client";

import { SmartLogo } from "@/components/common/smart-logo";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { isValidWebsite, normalizeWebsite, resolveProductLogoSources } from "@/lib/product-utils";
import type { Product } from "@/types/api";

export function WebsitePreview({ product }: { product: Product }) {
  const { t } = useSiteLocale();
  const website = normalizeWebsite(product.website);
  const verified = isValidWebsite(website) && !product.needs_verification;
  const brand = <>
    <SmartLogo className="research-product__logo" name={product.name} {...resolveProductLogoSources(product)} website={product.website} sourceUrl={product.source_url} trustPrimaryLogo size={56} />
    <span className="website-preview__identity"><strong>{product.name}</strong><span>{verified ? new URL(website).hostname : t("查找官网", "Website pending verification")}</span></span>
    <span className="website-preview__action">{verified ? t("打开官网", "Open website") : t("请参考原始资料", "Refer to the original source")} {verified ? <span aria-hidden="true">↗</span> : null}</span>
  </>;
  return verified ? <a className="website-preview" href={website} target="_blank" rel="noopener noreferrer">{brand}</a> : <div className="website-preview">{brand}</div>;
}
