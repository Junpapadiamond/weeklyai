import { isPlaceholderValue } from "./product-utils";

/** An absent record is not a zero or a fact worth giving its own display slot. */
export function detailValue(value?: string | null): string | null {
  const text = value?.trim();
  return !text || isPlaceholderValue(text) || /^[\s\-–—]+$/.test(text) ? null : text;
}

export function detailDate(value?: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? date.toISOString().slice(0, 10) : null;
}
