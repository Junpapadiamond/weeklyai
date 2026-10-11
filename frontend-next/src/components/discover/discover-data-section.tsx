import { DiscoverClient } from "@/components/discover/discover-client";
import { getDiscoveryPage } from "@/lib/api-client";

export async function DiscoverDataSection() {
  const initialPage = await getDiscoveryPage();
  return <DiscoverClient initialPage={initialPage} />;
}
