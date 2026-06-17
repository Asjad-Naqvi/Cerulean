from typing import Literal, Optional, List, Union, Dict, Any
from pydantic import BaseModel, Field

class ParsedQuery(BaseModel):
    item_type: Optional[str] = Field(default=None, description="The type of garment, e.g., kurta, shirt, trousers (lowercase)")
    color: Optional[str] = Field(default=None, description="Color of the garment, optional")
    material: Optional[str] = Field(default=None, description="Material of the garment, e.g., lawn, linen, cotton, silk, optional")
    gender: Literal["men", "women", "kids", "unisex", "any"] = Field(default="any", description="Target gender")
    price_tier: Literal["budget", "mid", "premium", "luxury", "any"] = Field(default="any", description="Price tier category")
    style_category: Optional[str] = Field(default=None, description="Style category, e.g., eastern, western, casual, formal, optional")
    min_price: Optional[float] = Field(default=None, description="Minimum price in PKR, optional")
    max_price: Optional[float] = Field(default=None, description="Maximum price in PKR, optional")
    generic_size: Optional[str] = Field(default=None, description="Generic size (XS, S, M, L, XL, XXL), optional")
    occasion: Optional[str] = Field(default=None, description="Occasion, e.g., casual, formal, bridal, wedding, optional")

class Product(BaseModel):
    id: str = Field(description="Unique product identifier (e.g., store_slug + original id)")
    store_name: str = Field(description="Display name of the store")
    store_slug: str = Field(description="Lowercased slug identifier of the store")
    title: str = Field(description="Product title")
    price: float = Field(description="Current selling price in PKR")
    compare_price: Optional[float] = Field(default=None, description="Original price before discount, in PKR (null if not on sale)")
    currency: str = Field(default="PKR", description="Currency code")
    available_sizes: List[str] = Field(default_factory=list, description="List of sizes currently in stock")
    matched_size: Optional[str] = Field(default=None, description="Determined size for the user if sizing info is provided")
    image_url: Optional[str] = Field(default=None, description="Primary product image URL")
    product_url: str = Field(description="Direct web link to product page")
    tags: List[str] = Field(default_factory=list, description="Cleaned product tags")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score assigned by ranker agent (0.0-1.0)")

class SearchResponse(BaseModel):
    results: List[Product] = Field(description="List of matching products")
    total_count: int = Field(description="Total count of results found")
    stores_queried: int = Field(description="Number of stores checked")
    stores_responded: int = Field(description="Number of stores that returned a valid response")
    failed_stores: List[str] = Field(description="Slugs of stores that failed or timed out")
    query_parsed: Union[ParsedQuery, Dict[str, Any]] = Field(description="The parsed user intent query")
    search_summary: str = Field(description="A friendly summarizing sentence from the Ranker agent")
    retrieval_iterations: int = Field(description="Number of search iterations / broadening loops executed")
    style_concept_image: Optional[str] = Field(default=None, description="Base64 encoded or URL of a style concept generated image for the query")
