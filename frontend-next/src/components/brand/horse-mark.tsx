import type { SVGProps } from "react";

/** The radar's horse: an angular mane, forward gaze, and a single signal. */
export function HorseMark({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 64 64" fill="none" className={className} aria-hidden="true" focusable="false" {...props}>
      <path
        fill="currentColor"
        fillRule="evenodd"
        d="M10 56c0-15 6-26 18-34L26 8l12 9 7 2 12 18-5 9-13-4-5-8c-2 8 0 16 8 22H10Zm31-30a2 2 0 1 0 4 0 2 2 0 0 0-4 0Z"
        clipRule="evenodd"
      />
      <path d="m12 34 9-4-8 12-5 3 4-11Z" fill="currentColor" />
      <circle cx="53" cy="12" r="4" fill="var(--primary, #dc4b5d)" />
    </svg>
  );
}
