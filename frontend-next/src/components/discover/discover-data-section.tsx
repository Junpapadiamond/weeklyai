import { DiscoverClient } from "@/components/discover/discover-client";
import { getWeeklyTop } from "@/lib/api-client";

const DISCOVER_PRODUCTS_LIMIT = 0;
const DISCOVER_DEFAULT_SORT = "composite";

export async function DiscoverDataSection() {
  const products = await getWeeklyTop(DISCOVER_PRODUCTS_LIMIT, DISCOVER_DEFAULT_SORT);
  return <DiscoverClient products={products} />;
}
