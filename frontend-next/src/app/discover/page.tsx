import { Suspense } from "react";
import { DiscoverDataSection } from "@/components/discover/discover-data-section";

function DiscoverSkeleton() {
  return (
    <section className="section">
      <div className="loading-block">加载随机发现中...</div>
    </section>
  );
}

export default function DiscoverPage() {
  return (
    <Suspense fallback={<DiscoverSkeleton />}>
      <DiscoverDataSection />
    </Suspense>
  );
}
