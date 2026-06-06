"use client";

import Link from "next/link";
import type { BlogPost, Product } from "@/types/api";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { HeroCard } from "@/components/home/hero-card";
import { RecentPicksStrip } from "@/components/home/recent-picks-strip";
import { NewsStream } from "@/components/home/news-stream";
import { parseLastUpdatedLabel } from "@/lib/api-client";

type HomeClientProps = {
  hero: Product | null;
  picks: Product[];
  blogs: BlogPost[];
  freshnessHoursAgo: number | null | undefined;
};

export function HomeClient({ hero, picks, blogs, freshnessHoursAgo }: HomeClientProps) {
  const { locale, t } = useSiteLocale();
  const issueNumber = Math.max(1, picks.length ? 120 + picks.length : 127);
  const today = new Date();
  const dateLabel = today.toLocaleDateString(locale, { month: "numeric", day: "numeric" });

  return (
    <div className="v2-home-root">
      <header className="v2-mast">
        <Link href="/" className="v2-brand" aria-label="WeeklyAI">
          WeeklyAI
        </Link>
        <div className="v2-mast__meta">
          <span>No.{issueNumber}</span>
          <span>{parseLastUpdatedLabel(freshnessHoursAgo, locale)}</span>
        </div>
      </header>

      <HeroCard product={hero} issueNumber={issueNumber} dateLabel={dateLabel} />

      <section className="v2-rubric-panel" aria-label={t("v2 选品方式", "v2 picking method")}>
        <span>{t("新的选品方式", "New picking method")}</span>
        <p>
          {t(
            "只看一个问题：AI 圈的人刷到会不会停下点开？融资只是背景，大厂也可以入选，但必须是新形态、新行为、新交互、意外组合，或把真实问题解决得明显更好。",
            "One test: would an AI-curious person stop scrolling and click? Funding is only context. Big labs can qualify, but only for new form, behavior, interaction, unexpected combo, or a clearly better solution to a real problem."
          )}
        </p>
      </section>

      <RecentPicksStrip picks={picks} />

      <NewsStream blogs={blogs} />

      <footer className="v2-footer">
        {t(
          `WeeklyAI · No.${issueNumber} · ${today.getFullYear()}.${dateLabel} · curated by ChenJunHsu`,
          `WeeklyAI · No.${issueNumber} · ${today.getFullYear()}.${dateLabel} · curated by ChenJunHsu`
        )}
      </footer>
    </div>
  );
}
