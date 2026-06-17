import os
import json
from typing import List, Literal

# Load stores config
STORES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "stores.json")
try:
    with open(STORES_PATH, "r", encoding="utf-8") as f:
        STORES = json.load(f)
except Exception:
    STORES = []

# Get active stores
ACTIVE_STORES = [s for s in STORES if s.get("active", False)]

def select_target_stores_fn(
    price_tier: Literal["budget", "mid", "premium", "luxury", "any"] = "any",
    gender: Literal["men", "women", "kids", "unisex", "any"] = "any",
    item_type: str = "",
    style_category: str = ""
) -> List[str]:
    """
    Selects the list of store slugs to check based on filters.
    
    Args:
        price_tier: User price category choice ('budget', 'mid', 'premium', 'luxury', 'any').
        gender: Target user gender ('men', 'women', 'kids', 'unisex', 'any').
        item_type: Specific garment type (e.g., 'kurta').
        style_category: Specific style (e.g., 'eastern').
        
    Returns:
        List of matching store slug strings.
    """
    if not ACTIVE_STORES:
        return []
 
    matched_slugs = []
    
    # Define price tier sets based on mapping:
    # budget -> [budget]
    # mid -> [budget, mid]
    # premium -> [mid, premium]
    # luxury -> [premium, luxury]
    price_map = {
        "budget": {"budget"},
        "mid": {"budget", "mid"},
        "premium": {"mid", "premium"},
        "luxury": {"premium", "luxury"},
        "any": {"budget", "mid", "premium", "luxury"}
    }
    
    allowed_tiers = price_map.get(price_tier, price_map["any"])
    
    for store in ACTIVE_STORES:
        # Check price tier
        store_tier = store.get("price_tier", "mid")
        if store_tier not in allowed_tiers:
            continue
            
        # Check gender
        # Store gender matches if user wants 'any', or store gender is unisex/any, or exact match
        store_gender = store.get("gender", "any")
        gender_match = False
        if gender == "any":
            gender_match = True
        elif store_gender == "unisex" or store_gender == "any":
            gender_match = True
        elif gender == "unisex" and store_gender == "unisex":
            gender_match = True
        elif gender == store_gender:
            gender_match = True
            
        if not gender_match:
            continue
            
        # If we made it past filters, add to target
        matched_slugs.append(store["slug"])
        
    # Fallback: if no stores matched, return all active store slugs
    if not matched_slugs:
        matched_slugs = [store["slug"] for store in ACTIVE_STORES]
        
    return matched_slugs[:21]
