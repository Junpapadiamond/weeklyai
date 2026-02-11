export type ApiResponse<T> = {
  success?: boolean;
  data?: T;
  message?: string;
};

export type Product = {
  _id?: string;
  id?: string;
  name: string;
  website?: string;
  description: string;
  why_matters?: string;
  logo_url?: string;
  logo?: string;
  dark_horse_index?: number;
  category?: string;
  categories?: string[];
  hardware_category?: string;
  hardware_type?: string;
  form_factor?: string;
  use_case?: string;
  innovation_traits?: string[];
  price?: string;
  funding_total?: string;
  latest_news?: string;
  source?: string;
  source_url?: string;
  region?: string;
  final_score?: number;
  trending_score?: number;
  hot_score?: number;
  weekly_users?: number;
  first_seen?: string;
  published_at?: string;
  discovered_at?: string;
  is_hardware?: boolean;
  needs_verification?: boolean;
  extra?: Record<string, unknown>;
};

export type BlogPost = {
  name: string;
  description: string;
  website?: string;
  logo_url?: string;
  logo?: string;
  source?: string;
  published_at?: string;
  categories?: string[];
  content_type?: string;
  final_score?: number;
  trending_score?: number;
  dark_horse_index?: number;
  extra?: Record<string, unknown>;
};

export type IndustryLeaderProduct = {
  name: string;
  company?: string;
  website?: string;
  logo?: string;
  region?: string;
  description?: string;
  founded?: string;
  funding?: string;
  valuation?: string;
  users?: string;
  why_famous?: string;
};

export type IndustryLeaderCategory = {
  icon?: string;
  description?: string;
  products: IndustryLeaderProduct[];
};

export type IndustryLeadersPayload = {
  _meta?: {
    description?: string;
    note?: string;
    last_updated?: string;
  };
  categories: Record<string, IndustryLeaderCategory>;
};

export type LastUpdatedPayload = {
  last_updated?: string | null;
  hours_ago?: number | null;
};

export type SearchParams = {
  q?: string;
  categories?: string[];
  type?: "all" | "software" | "hardware";
  sort?: "trending" | "rating" | "users";
  page?: number;
  limit?: number;
};
