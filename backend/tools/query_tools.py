from typing import Literal, Optional
from models.schemas import ParsedQuery

def parse_text_query_fn(
    item_type: Optional[str] = None,
    color: Optional[str] = None,
    material: Optional[str] = None,
    gender: Literal["men", "women", "kids", "unisex", "any"] = "any",
    price_tier: Literal["budget", "mid", "premium", "luxury", "any"] = "any",
    style_category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    generic_size: Optional[str] = None,
    occasion: Optional[str] = None
) -> dict:
    """
    Submit the extracted query parameters from user's text search query.
    Use this tool to output the structured search parameters.
    """
    try:
        query = ParsedQuery(
            item_type=item_type,
            color=color,
            material=material,
            gender=gender,
            price_tier=price_tier,
            style_category=style_category,
            min_price=min_price,
            max_price=max_price,
            generic_size=generic_size,
            occasion=occasion
        )
        return query.model_dump()
    except Exception:
        return ParsedQuery().model_dump()

def parse_image_query_fn(
    item_type: Optional[str] = None,
    color: Optional[str] = None,
    material: Optional[str] = None,
    gender: Literal["men", "women", "kids", "unisex", "any"] = "any",
    price_tier: Literal["budget", "mid", "premium", "luxury", "any"] = "any",
    style_category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    generic_size: Optional[str] = None,
    occasion: Optional[str] = None
) -> dict:
    """
    Submit the extracted query parameters from user's image upload search query.
    Use this tool to output the structured search parameters.
    """
    try:
        query = ParsedQuery(
            item_type=item_type,
            color=color,
            material=material,
            gender=gender,
            price_tier=price_tier,
            style_category=style_category,
            min_price=min_price,
            max_price=max_price,
            generic_size=generic_size,
            occasion=occasion
        )
        return query.model_dump()
    except Exception:
        return ParsedQuery().model_dump()
