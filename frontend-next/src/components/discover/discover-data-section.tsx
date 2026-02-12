import { DiscoverClient } from "@/components/discover/discover-client";
import { getWeeklyTop } from "@/lib/api-client";

const DISCOVER_PRODUCTS_LIMIT = 0;

export async function DiscoverDataSection() {
  const products = await getWeeklyTop(DISCOVER_PRODUCTS_LIMIT);
  return <DiscoverClient products={products} />;
}
