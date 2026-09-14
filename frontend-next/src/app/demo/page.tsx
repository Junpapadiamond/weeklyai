import type { Metadata } from "next";
import { DemoGallery } from "@/components/demo/demo-gallery";
export const metadata: Metadata = { title: "交互演示 · WeeklyAI", description: "无需注册，直接体验 AI 产品的完整工作流程。" };
export default async function DemoPage({ searchParams }: { searchParams: Promise<{ filter?: string }> }) {
  const filter = (await searchParams).filter === "ready" ? "ready" : "all";
  return <DemoGallery key={filter} initialFilter={filter} />;
}
