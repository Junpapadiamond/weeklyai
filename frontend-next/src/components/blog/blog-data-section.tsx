import { BlogClient } from "@/components/blog/blog-client";
import { getBlogs } from "@/lib/api-client";
import type { BlogPost } from "@/types/api";

const BLOG_PREFETCH_LIMIT = 120;

export async function BlogDataSection() {
  let initialBlogs: BlogPost[] = [];

  try {
    initialBlogs = await getBlogs("", BLOG_PREFETCH_LIMIT, "hybrid");
  } catch (error) {
    console.warn("Failed to preload blog data, fallback to empty list", error);
  }

  return <BlogClient initialBlogs={initialBlogs} />;
}
