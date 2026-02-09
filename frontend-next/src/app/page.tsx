import { Suspense } from "react";
import { HomeDataSection } from "@/components/home/home-data-section";

function HomeSkeleton() {
  return (
    <div className="section">
      <div className="loading-block">正在加载首页数据...</div>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<HomeSkeleton />}>
      <HomeDataSection />
    </Suspense>
  );
}
