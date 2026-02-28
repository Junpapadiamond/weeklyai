"use client";

import { Heart } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { BlogPost, Product } from "@/types/api";
import { useSiteLocale } from "@/components/layout/locale-provider";
import {
  isBlogFavorited,
  isProductFavorited,
  subscribeFavorites,
  toggleBlogFavorite,
  toggleProductFavorite,
} from "@/lib/favorites";

type FavoriteButtonProps = {
  product?: Product;
  blog?: BlogPost;
  className?: string;
  size?: "sm" | "md";
  showLabel?: boolean;
};

export function FavoriteButton({ product, blog, className = "", size = "sm", showLabel = false }: FavoriteButtonProps) {
  const { t } = useSiteLocale();
  const mode = blog ? "blog" : "product";
  const fingerprint = useMemo(() => {
    if (blog) {
      return [blog.name, blog.website, blog.source, blog.published_at].join("::");
    }
    if (product) {
      return [product._id, product.id, product.name, product.website].join("::");
    }
    return "unknown";
  }, [blog, product]);
  const [favorited, setFavorited] = useState(false);

  useEffect(() => {
    const syncState = () => {
      if (mode === "blog" && blog) {
        setFavorited(isBlogFavorited(blog));
        return;
      }
      if (mode === "product" && product) {
        setFavorited(isProductFavorited(product));
      }
    };

    syncState();
    return subscribeFavorites(syncState);
  }, [blog, mode, product, fingerprint]);

  if (!blog && !product) return null;

  const offLabel = t("收藏", "Favorite");
  const onLabel = t("已收藏", "Saved");
  const removeLabel = t("取消收藏", "Remove favorite");

  return (
    <button
      className={`favorite-btn favorite-btn--${size} ${favorited ? "is-active" : ""} ${className}`.trim()}
      type="button"
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        if (mode === "blog" && blog) {
          setFavorited(toggleBlogFavorite(blog));
          return;
        }
        if (mode === "product" && product) {
          setFavorited(toggleProductFavorite(product));
        }
      }}
      aria-pressed={favorited}
      aria-label={favorited ? removeLabel : offLabel}
      title={favorited ? removeLabel : offLabel}
    >
      <Heart size={size === "sm" ? 14 : 16} />
      {showLabel ? <span>{favorited ? onLabel : offLabel}</span> : null}
    </button>
  );
}
