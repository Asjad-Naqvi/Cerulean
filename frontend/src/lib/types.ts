export interface ParsedQuery {
  item_type: string | null;
  color: string | null;
  material: string | null;
  gender: 'men' | 'women' | 'kids' | 'unisex' | 'any';
  price_tier: 'budget' | 'mid' | 'premium' | 'luxury' | 'any';
  style_category: string | null;
  min_price: number | null;
  max_price: number | null;
  generic_size: string | null;
  occasion: string | null;
}

export interface Product {
  id: string;
  store_name: string;
  store_slug: string;
  title: string;
  price: number;
  compare_price: number | null;
  currency: string;
  available_sizes: string[];
  matched_size: string | null;
  image_url: string | null;
  product_url: string;
  tags: string[];
  relevance_score: number | null;
}

export interface SearchResponse {
  results: Product[];
  total_count: number;
  stores_queried: number;
  stores_responded: number;
  failed_stores: string[];
  query_parsed: ParsedQuery;
  search_summary: string;
  retrieval_iterations: number;
  style_concept_image?: string | null;
}

export interface Measurements {
  chest?: number;
  waist?: number;
  hips?: number;
}

