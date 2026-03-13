export const IOS_APP_SHELL_UA_MARKER = "WeeklyAIApp-iOS/1.0";
const IOS_APP_SHELL_UA_PREFIX = "WeeklyAIApp-iOS/";

export function isAppShellUserAgent(userAgent: string | null | undefined): boolean {
  const normalized = String(userAgent || "").trim();
  if (!normalized) return false;
  return normalized.includes(IOS_APP_SHELL_UA_MARKER) || normalized.includes(IOS_APP_SHELL_UA_PREFIX);
}

export function isAppShell(): boolean {
  if (typeof window === "undefined") return false;
  return isAppShellUserAgent(window.navigator.userAgent);
}
