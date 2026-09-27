import { DemoExplorer } from "@/components/demo/demo-explorer";
import { getWeeklyTop } from "@/lib/api-client";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";
import "@/styles/demo-legacy.css";

export const dynamic = "force-dynamic";
export async function generateMetadata() {
  const locale = await getRequestLocale();
  return { title: pickLocaleText(locale, { zh: "演示示例", en: "Interactive examples" }) };
}

export default async function DemoExamplesPage() {
  const products = await getWeeklyTop(0, "composite");
  return <div className="legacy-demo-surface"><DemoExplorer products={products} /></div>;
}
