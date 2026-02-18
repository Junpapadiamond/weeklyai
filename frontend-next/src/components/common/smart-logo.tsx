"use client";

import { useMemo, useState } from "react";
import { getLogoCandidates, getMonogram } from "@/lib/product-utils";

type SmartLogoProps = {
  className?: string;
  name?: string;
  logoUrl?: string;
  secondaryLogoUrl?: string;
  website?: string;
  sourceUrl?: string;
  size?: number;
  loading?: "lazy" | "eager";
};

export function SmartLogo({
  className,
  name,
  logoUrl,
  secondaryLogoUrl,
  website,
  sourceUrl,
  size = 48,
  loading = "lazy",
}: SmartLogoProps) {
  const monogram = getMonogram(name);
  const candidates = useMemo(
    () =>
      getLogoCandidates({
        logoUrl,
        secondaryLogoUrl,
        website,
        sourceUrl,
      }),
    [logoUrl, secondaryLogoUrl, sourceUrl, website]
  );
  const [index, setIndex] = useState(0);
  const [isExhausted, setIsExhausted] = useState(false);
  const current = !isExhausted ? candidates[index] : undefined;

  const moveToNextCandidate = () => {
    if (index + 1 < candidates.length) {
      setIndex((prev) => prev + 1);
      return;
    }
    setIsExhausted(true);
  };

  return (
    <span className={className} aria-hidden="true">
      {current ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={current}
          alt=""
          width={size}
          height={size}
          loading={loading}
          decoding="async"
          onLoad={(event) => {
            if (event.currentTarget.naturalWidth > 0 && event.currentTarget.naturalHeight > 0) return;
            moveToNextCandidate();
          }}
          onError={moveToNextCandidate}
        />
      ) : (
        <span className="smart-logo__fallback">{monogram}</span>
      )}
    </span>
  );
}
