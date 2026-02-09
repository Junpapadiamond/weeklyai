"use client";

import { useMemo, useState } from "react";
import { getLogoCandidates, getMonogram } from "@/lib/product-utils";

type SmartLogoProps = {
  className?: string;
  name?: string;
  logoUrl?: string;
  website?: string;
  sourceUrl?: string;
  size?: number;
};

export function SmartLogo({ className, name, logoUrl, website, sourceUrl, size = 48 }: SmartLogoProps) {
  const monogram = getMonogram(name);
  const candidates = useMemo(
    () =>
      getLogoCandidates({
        logoUrl,
        website,
        sourceUrl,
      }),
    [logoUrl, sourceUrl, website]
  );
  const [index, setIndex] = useState(0);
  const [isExhausted, setIsExhausted] = useState(false);
  const current = !isExhausted ? candidates[index] : undefined;

  return (
    <span className={className} aria-hidden="true">
      {current ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={current}
          alt=""
          width={size}
          height={size}
          loading="lazy"
          decoding="async"
          onError={() => {
            if (index + 1 < candidates.length) {
              setIndex((prev) => prev + 1);
              return;
            }
            setIsExhausted(true);
          }}
        />
      ) : (
        <span>{monogram}</span>
      )}
    </span>
  );
}
