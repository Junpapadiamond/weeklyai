import { Suspense } from "react";
import { BlogClient } from "@/components/blog/blog-client";

export const metadata = {
  title: "WeeklyAI - 博客动态",
};

export default function BlogPage() {
  return (
    <Suspense fallback={<div className="section"><div className="loading-block">加载博客中...</div></div>}>
      <BlogClient />
    </Suspense>
  );
}
