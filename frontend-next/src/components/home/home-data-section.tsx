import { HomeClient } from "@/components/home/home-client";
import { getDarkHorses, getLastUpdated, getWeeklyTop } from "@/lib/api-client";

const HOME_INITIAL_PRODUCTS_LIMIT = 120;
const DARK_HORSE_FETCH_LIMIT = 30;
const HOME_DEFAULT_SORT = "recency";

export async function HomeDataSection() {
  const [darkHorses, allProducts, lastUpdated] = await Promise.all([
    getDarkHorses(DARK_HORSE_FETCH_LIMIT, 4),
    getWeeklyTop(HOME_INITIAL_PRODUCTS_LIMIT, HOME_DEFAULT_SORT),
    getLastUpdated(),
  ]);

  return (
    <HomeClient
      darkHorses={darkHorses}
      allProducts={allProducts}
      freshnessHoursAgo={lastUpdated.hours_ago}
    />
  );
}
