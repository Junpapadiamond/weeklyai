"use client";

import { Share2 } from "lucide-react";
import { useState } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";

type ProductShareButtonProps = {
  productName: string;
};

export function ProductShareButton({ productName }: ProductShareButtonProps) {
  const { t } = useSiteLocale();
  const [copied, setCopied] = useState(false);

  async function handleShare() {
    const shareUrl = window.location.href;

    if (navigator.share) {
      try {
        await navigator.share({
          title: productName,
          text: t("看看这个值得关注的 AI 产品。", "Check out this AI product."),
          url: shareUrl,
        });
        return;
      } catch {
        // Fall back to clipboard when native share is dismissed or unavailable.
      }
    }

    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button type="button" className={`link-btn ${copied ? "is-success" : ""}`} onClick={handleShare}>
      <Share2 size={14} /> {copied ? t("已复制链接", "Link copied") : t("分享", "Share")}
    </button>
  );
}
