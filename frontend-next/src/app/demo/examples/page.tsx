import { DemoExplorer } from "@/components/demo/demo-explorer";
import { getWeeklyTop } from "@/lib/api-client";
import "@/styles/demo-legacy.css";

export const dynamic = "force-dynamic";
export const metadata = { title: "Interactive examples" };

export default async function DemoExamplesPage() {
  const products = await getWeeklyTop(0, "composite");
  return <div className="legacy-demo-surface"><DemoExplorer products={products} /></div>;
}
