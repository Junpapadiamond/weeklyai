import type { MouseEvent } from "react";
import { isAppShell } from "@/lib/app-shell";

function normalizeExternalUrl(url: string): string {
  const value = String(url || "").trim();
  if (!value) return "";
  try {
    const parsed = new URL(value);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return "";
    return parsed.toString();
  } catch {
    return "";
  }
}

export function openExternalUrl(url: string): void {
  if (typeof window === "undefined") return;
  const normalized = normalizeExternalUrl(url);
  if (!normalized) return;

  if (isAppShell()) {
    window.location.assign(normalized);
    return;
  }

  window.open(normalized, "_blank", "noopener,noreferrer");
}

export function handleExternalAnchorClick(event: MouseEvent<HTMLAnchorElement>, url: string): void {
  if (!isAppShell()) return;
  event.preventDefault();
  openExternalUrl(url);
}
