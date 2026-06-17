import json
from typing import Union, List, Dict, Any

def filter_products_fn(
    raw_products_json: str,
    parsed_query_json: str
) -> dict:
    """
    Filters a list of normalized products based on query constraints.
    
    Args:
        raw_products_json: JSON string or list of normalized product dicts.
        parsed_query_json: JSON string or dict of the parsed search query.
        
    Returns:
        Dict containing the list of filtered products: {"products": [...]}
    """
    # Parse inputs if they are strings
    if isinstance(raw_products_json, str):
        try:
            products = json.loads(raw_products_json)
        except Exception:
            products = []
    else:
        products = raw_products_json

    if isinstance(parsed_query_json, str):
        try:
            query = json.loads(parsed_query_json)
        except Exception:
            query = {}
    else:
        query = parsed_query_json

    if not isinstance(products, list):
        return {"products": []}

    filtered = []
    
    item_type = query.get("item_type")
    color = query.get("color")
    material = query.get("material")
    min_price = query.get("min_price")
    max_price = query.get("max_price")
    
    # Pre-parse synonym mapping for item_type if present
    it_words = []
    if item_type:
        it_val = str(item_type).lower()
        it_words = [w for w in it_val.replace("-", " ").split() if len(w) > 2]
        
    synonyms = {
        "kameez": {"kameez", "kurta", "kurti", "shirt", "top", "suit", "set"},
        "kurta": {"kameez", "kurta", "kurti", "shirt", "top", "suit", "set"},
        "kurti": {"kameez", "kurta", "kurti", "shirt", "top", "suit", "set"},
        "shalwar": {"shalwar", "pant", "pants", "trouser", "trousers", "pajama", "bottom", "suit", "set"},
        "trouser": {"shalwar", "pant", "pants", "trouser", "trousers", "pajama", "bottom", "suit", "set"},
        "trousers": {"shalwar", "pant", "pants", "trouser", "trousers", "pajama", "bottom", "suit", "set"}
    }
    
    for prod in products:
        # Check min price
        if min_price is not None:
            try:
                if prod.get("price", 0.0) < float(min_price):
                    continue
            except (ValueError, TypeError):
                pass
                
        # Check max price
        if max_price is not None:
            try:
                if prod.get("price", 0.0) > float(max_price):
                    continue
            except (ValueError, TypeError):
                pass
                
        title_lower = prod.get("title", "").lower()
        tags_lower = [str(t).lower() for t in prod.get("tags", [])]
        combined_text = title_lower + " " + " ".join(tags_lower)
        
        # Match item type
        if it_words:
            matched_it = False
            for w in it_words:
                if w in combined_text:
                    matched_it = True
                    break
                if w in synonyms:
                    for syn in synonyms[w]:
                        if syn in combined_text:
                            matched_it = True
                            break
                    if matched_it:
                        break
            if not matched_it:
                continue
                
        # Match color
        if color:
            c_val = str(color).lower()
            if c_val not in combined_text:
                continue
                
        # Match material
        if material:
            m_val = str(material).lower()
            if m_val not in combined_text:
                continue
                
        filtered.append(prod)
        
    # Sort by price ascending
    filtered.sort(key=lambda p: p.get("price", 0.0))
    
    return {"products": filtered}
