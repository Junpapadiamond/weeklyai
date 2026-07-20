import { HomeClient } from "@/components/home/home-client";
import { getBlogs, getHeroProduct, getLastUpdated, getPicks } from "@/lib/api-client";

const RECENT_PICKS_LIMIT = 7;
const HOME_NEWS_LIMIT = 12;

export async function HomeDataSection() {
  const [hero, picks, blogs, lastUpdated] = await Promise.all([
    getHeroProduct(),
    getPicks(RECENT_PICKS_LIMIT),
    getBlogs("", HOME_NEWS_LIMIT, "hybrid"),
    getLastUpdated(),
  ]);

  return (
    <HomeClient
      hero={hero}
      picks={picks}
      blogs={blogs}
      freshnessHoursAgo={lastUpdated.hours_ago}
    />
  );
}
