import type { CapacitorConfig } from "@capacitor/cli";

const appUrl = (process.env.WEEKLYAI_WEB_URL || "https://weeklyai.vercel.app").trim();
const apiUrl = (process.env.WEEKLYAI_API_URL || "https://weeklyai-api.vercel.app/api/v1").trim();

function hostFrom(url: string, fallback: string) {
  try {
    return new URL(url).host;
  } catch {
    return fallback;
  }
}

const config: CapacitorConfig = {
  appId: "com.weeklyai.app",
  appName: "WeeklyAI",
  webDir: "web",
  appendUserAgent: "WeeklyAIApp-iOS/1.0",
  server: {
    url: appUrl,
    cleartext: false,
    allowNavigation: [
      hostFrom(appUrl, "weeklyai.vercel.app"),
      hostFrom(apiUrl, "weeklyai-api.vercel.app"),
    ],
  },
  ios: {
    contentInset: "automatic",
    scrollEnabled: true,
    preferredContentMode: "mobile",
    limitsNavigationsToAppBoundDomains: false,
    backgroundColor: "#0B1020",
    appendUserAgent: "WeeklyAIApp-iOS/1.0",
  },
};

export default config;
