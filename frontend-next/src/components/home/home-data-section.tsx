import { HomeClient } from "@/components/home/home-client";
import { getDarkHorses, getLastUpdated, getWeeklyTop, parseLastUpdatedLabel } from "@/lib/api-client";

const HOME_INITIAL_PRODUCTS_LIMIT = 0;
const DARK_HORSE_FETCH_LIMIT = 30;
const HOME_DEFAULT_SORT = "composite";

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
      freshnessLabel={parseLastUpdatedLabel(lastUpdated.hours_ago)}
    />
  );
}
