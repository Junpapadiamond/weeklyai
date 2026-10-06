"use client";

import { useCallback, useEffect, useRef, useMemo, useState } from "react";
import Image from "next/image";
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
  return <LogoImage key={JSON.stringify(candidates)} candidates={candidates} monogram={monogram} className={className} size={size} loading={loading} />;
}

function LogoImage({ candidates, monogram, className, size, loading }: {
  candidates: string[]; monogram: string; className?: string; size: number; loading: "lazy" | "eager";
}) {
  const [index, setIndex] = useState(0);
  const current = candidates[index];
  const Logo = current?.startsWith("/logos/verified/") && !current.endsWith(".svg") ? Image : "img";
  const imgRef = useRef<HTMLImageElement>(null);
  // onError, hydration and the timeout may all observe the same failure.
  // Advance exactly once, and ignore late events from a previous candidate.
  const moveToNextCandidate = useCallback(() => {
    setIndex(previous => previous === index ? previous + 1 : previous);
  }, [index]);

  // If the image finished loading/erroring before React hydrated and attached
  // onError, the error event is permanently missed. Check img.complete on each
  // candidate change to catch those pre-hydration failures.
  useEffect(() => {
    const img = imgRef.current;
    if (!img || !current) return;
    if (img.complete) {
      if (!img.naturalWidth || !img.naturalHeight) {
        const timer = setTimeout(moveToNextCandidate, 0);
        return () => clearTimeout(timer);
      }
      return;
    }
    let timer: ReturnType<typeof setTimeout> | undefined;
    const start = () => {
      if (timer) return;
      timer = setTimeout(() => {
        if (!img.complete || !img.naturalWidth) moveToNextCandidate();
      }, 5000);
    };
    // Lazy images below the fold must not time out before loading starts.
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) { start(); observer.disconnect(); }
    }, { rootMargin: "200px" });
    if (loading === "eager") start();
    else observer.observe(img);
    return () => { clearTimeout(timer); observer.disconnect(); };
  }, [current, loading, moveToNextCandidate]);

  return (
    <span className={className} aria-hidden="true">
      {current ? (
        <Logo
          key={current}
          ref={imgRef}
          src={current}
          alt=""
          width={size}
          height={size}
          sizes={`${size}px`}
          loading={loading}
          decoding="async"
          referrerPolicy="no-referrer"
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
