import Form from "next/form";
import Link from "next/link";
import { ArrowUpRight, MagnifyingGlass, PlayCircle, Shuffle } from "@phosphor-icons/react";

type ChineseHomeIntroProps = {
  categories: { value: string; label: string }[];
  onCategorySelect: (value: string) => void;
};

export function ChineseHomeIntro({ categories, onCategorySelect }: ChineseHomeIntroProps) {
  return (
    <section className="cn-home-intro" aria-labelledby="home-heading">
      <div className="cn-home-intro__main">
        <h1 id="home-heading">发现 AI 新产品</h1>
        <Form action="/search" className="cn-home-search" role="search" aria-label="搜索产品">
          <MagnifyingGlass size={20} aria-hidden="true" />
          <input name="q" type="search" aria-label="产品名称或关键词" placeholder="搜索产品名称或用途" required maxLength={200} />
          <button type="submit">搜索</button>
        </Form>
        <nav className="cn-home-categories" aria-label="按分类浏览">
          {categories.map((category) => (
            <a key={category.value} href="#trendingSection" onClick={() => onCategorySelect(category.value)}>{category.label}</a>
          ))}
        </nav>
      </div>
      <aside className="cn-home-shortcuts" aria-label="更多发现方式">
        <Link href="/discover">
          <Shuffle size={21} aria-hidden="true" />
          <span><strong>随便看看</strong></span>
          <ArrowUpRight size={17} aria-hidden="true" />
        </Link>
        <Link href="/demo">
          <PlayCircle size={21} aria-hidden="true" />
          <span><strong>产品演示</strong></span>
          <ArrowUpRight size={17} aria-hidden="true" />
        </Link>
      </aside>
    </section>
  );
}
