"use client";

import { useMemo, useState } from "react";
import { SmartLogo } from "@/components/common/smart-logo";
import { isValidWebsite, normalizeWebsite } from "@/lib/product-utils";

type WebsiteScreenshotProps = {
  className?: string;
  website?: string;
  name?: string;
  logoUrl?: string;
  secondaryLogoUrl?: string;
  sourceUrl?: string;
  alt?: string;
  logoSize?: number;
};

function getThumioUrl(website?: string): string {
  const normalized = normalizeWebsite(website);
  if (!isValidWebsite(normalized)) return "";
  return `https://image.thum.io/get/width/1200/crop/900/noanimate/${encodeURI(normalized)}`;
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
  const [failed, setFailed] = useState(false);
  const screenshotUrl = useMemo(() => getThumioUrl(website), [website]);
  const showImage = !!screenshotUrl && !failed;

  return (
    <div className={`website-shot ${className || ""}`}>
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          className="website-shot__image"
          src={screenshotUrl}
          alt={alt || `${name || "产品"} 官网截图`}
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="website-shot__fallback" aria-label="官网截图加载失败，已显示 Logo">
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
