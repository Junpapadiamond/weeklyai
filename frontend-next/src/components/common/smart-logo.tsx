"use client";

import { useEffect, useRef, useMemo, useState } from "react";
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
  trustPrimaryLogo?: boolean;
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
  trustPrimaryLogo = false,
}: SmartLogoProps) {
  const monogram = getMonogram(name);
  const candidates = useMemo(
    () =>
      getLogoCandidates({
        logoUrl,
        secondaryLogoUrl,
        website,
        sourceUrl,
        trustPrimaryLogo,
      }),
    [logoUrl, secondaryLogoUrl, sourceUrl, trustPrimaryLogo, website]
  );
  const [index, setIndex] = useState(0);
  const [isExhausted, setIsExhausted] = useState(false);
  const current = !isExhausted ? candidates[index] : undefined;
  const imgRef = useRef<HTMLImageElement>(null);

  const moveToNextCandidate = () => {
    if (index + 1 < candidates.length) {
      setIndex((prev) => prev + 1);
      return;
    }
    setIsExhausted(true);
  };

  // If the image finished loading/erroring before React hydrated and attached
  // onError, the error event is permanently missed. Check img.complete on each
  // candidate change to catch those pre-hydration failures.
  useEffect(() => {
    const img = imgRef.current;
    if (!img || !img.complete) return;
    if (img.naturalWidth > 0 && img.naturalHeight > 0) return;
    moveToNextCandidate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current]);

  return (
    <span className={className} aria-hidden="true">
      {current ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          ref={imgRef}
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
