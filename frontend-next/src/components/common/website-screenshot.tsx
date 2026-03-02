"use client";

import { useMemo, useState } from "react";
import { SmartLogo } from "@/components/common/smart-logo";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { isValidWebsite, normalizeWebsite } from "@/lib/product-utils";

type WebsiteScreenshotProps = {
  className?: string;
  website?: string;
  name?: string;
  logoUrl?: string;
  secondaryLogoUrl?: string;
  sourceUrl?: string;
  category?: string;
  categories?: string[];
  isHardware?: boolean;
  alt?: string;
  logoSize?: number;
};

function getThumioUrl(website?: string): string {
  const normalized = normalizeWebsite(website);
  if (!isValidWebsite(normalized)) return "";
  return `https://image.thum.io/get/width/1200/noanimate/${encodeURI(normalized)}`;
}

export function WebsiteScreenshot({
  className,
  website,
  name,
  logoUrl,
  secondaryLogoUrl,
  sourceUrl,
  alt,
  logoSize = 44,
}: WebsiteScreenshotProps) {
  const { t } = useSiteLocale();
  const screenshotUrl = useMemo(() => getThumioUrl(website), [website]);
  const [failed, setFailed] = useState(false);
  const showImage = !!screenshotUrl && !failed;

  return (
    <div className={`website-shot ${className || ""}`}>
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          className="website-shot__image"
          src={screenshotUrl}
          alt={alt || `${name || t("产品", "product")} ${t("官网截图", "website screenshot")}`}
          crossOrigin="anonymous"
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="website-shot__fallback" aria-label={t("官网截图加载失败，已显示 Logo", "Website screenshot failed to load, showing logo")}>
          <SmartLogo
            className="website-shot__logo"
            name={name}
            logoUrl={logoUrl}
            secondaryLogoUrl={secondaryLogoUrl}
            website={website}
            sourceUrl={sourceUrl}
            size={logoSize}
          />
        </div>
      )}
    </div>
  );
}
