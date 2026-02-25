import { Suspense } from "react";
import { BlogDataSection } from "@/components/blog/blog-data-section";

export const metadata = {
  title: "WeeklyAI - 博客动态",
};

export default function BlogPage() {
  return (
    <Suspense fallback={<div className="section"><div className="loading-block">加载博客中...</div></div>}>
      <BlogDataSection />
    </Suspense>
  );
}
