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
        <p className="cn-home-intro__label"><span className="signal-dot" /> 黑马雷达 · AI 产品发现</p>
        <h1 id="home-heading">发现 AI 新产品</h1>
        <p className="cn-home-intro__description">找实用工具，也找产品灵感。看看海内外的新产品都在解决什么问题。</p>
        <Form action="/search" className="cn-home-search" role="search" aria-label="搜索产品">
          <MagnifyingGlass size={20} aria-hidden="true" />
          <input name="q" type="search" aria-label="产品名称或关键词" placeholder="搜索产品名称或用途" required maxLength={200} />
          <button type="submit">搜索</button>
        </Form>
        <nav className="cn-home-categories" aria-label="按分类浏览">
          <span>按分类找</span>
          {categories.map((category) => (
            <a key={category.value} href="#trendingSection" onClick={() => onCategorySelect(category.value)}>{category.label}</a>
          ))}
        </nav>
      </div>
      <aside className="cn-home-shortcuts" aria-label="更多发现方式">
        <Link href="/discover">
          <Shuffle size={21} aria-hidden="true" />
          <span><strong>随便看看</strong><small>一次看一款，喜欢就收藏</small></span>
          <ArrowUpRight size={17} aria-hidden="true" />
        </Link>
        <Link href="/demo">
          <PlayCircle size={21} aria-hidden="true" />
          <span><strong>看产品演示</strong><small>用示例了解产品怎么用</small></span>
          <ArrowUpRight size={17} aria-hidden="true" />
        </Link>
        <Link className="cn-home-shortcuts__about" href="/content-sources">黑马和潜力股怎么选？<ArrowUpRight size={14} aria-hidden="true" /></Link>
      </aside>
    </section>
  );
}
