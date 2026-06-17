import os
import json
from typing import Union, List, Dict, Any, Optional

SIZE_CHARTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "size_charts.json")
try:
    with open(SIZE_CHARTS_PATH, "r", encoding="utf-8") as f:
        SIZE_CHARTS = json.load(f)
except Exception:
    SIZE_CHARTS = {}

# Standard fallback size chart
FALLBACK_CHART = {
    "XS": {"chest": 32.0, "waist": 26.0, "hips": 35.0},
    "S": {"chest": 34.0, "waist": 28.0, "hips": 37.0},
    "M": {"chest": 38.0, "waist": 32.0, "hips": 41.0},
    "L": {"chest": 42.0, "waist": 36.0, "hips": 45.0},
    "XL": {"chest": 46.0, "waist": 40.0, "hips": 49.0}
}

def _resolve_size(store_slug: str, chest: float) -> Optional[str]:
    chart = SIZE_CHARTS.get(store_slug, FALLBACK_CHART)
    # Sort sizes by chest measurement ascending
    sorted_sizes = sorted(chart.items(), key=lambda item: item[1].get("chest", 0.0))
    
    for size_label, measurements in sorted_sizes:
        store_chest = measurements.get("chest", 0.0)
        if store_chest >= chest:
            return size_label
            
    return None

def map_product_sizes_fn(
    products_json: str,
    measurements_json: Optional[str] = None,
    generic_size: Optional[str] = None
) -> dict:
    """
    Maps user measurements or generic size to product sizes and filters out out-of-stock items.
    
    Args:
        products_json: List of products or JSON string representing them.
        measurements_json: Optional dict, JSON string or None containing chest/waist/hips.
        generic_size: Optional generic size label (e.g. 'M').
        
    Returns:
        Dict containing list of matched products: {"products": [...]}
    """
    if isinstance(products_json, str):
        try:
            products = json.loads(products_json)
        except Exception:
            products = []
    else:
        products = products_json

    if isinstance(measurements_json, str) and measurements_json:
        try:
            measurements = json.loads(measurements_json)
        except Exception:
            measurements = None
    else:
        measurements = measurements_json

    if not isinstance(products, list):
        return {"products": []}

    has_constraint = bool(generic_size or (measurements and "chest" in measurements))
    
    mapped_products = []
    
    for prod in products:
        store_slug = prod.get("store_slug", "")
        available_sizes = [str(s).upper() for s in prod.get("available_sizes", [])]
        
        matched_size = None
        
        # If measurements are provided, resolve size via chest measurement
        if measurements and "chest" in measurements:
            try:
                chest_val = float(measurements["chest"])
                matched_size = _resolve_size(store_slug, chest_val)
            except (ValueError, TypeError):
                pass
        
        # If no size was matched via measurements, but generic_size is specified, use generic_size
        if not matched_size and generic_size:
            matched_size = str(generic_size).upper()
            
        # If we have a size constraint, we must drop the product if the size is not available
        if has_constraint:
            if not matched_size or matched_size not in available_sizes:
                continue
                
        prod_copy = dict(prod)
        prod_copy["matched_size"] = matched_size
        mapped_products.append(prod_copy)
        
    return {"products": mapped_products}

def broaden_search_criteria_fn(
    parsed_query_json: str,
    strategy: str
) -> dict:
    """
    Broadens a search query's criteria to retrieve more products.
    
    Args:
        parsed_query_json: JSON string or dict of the current query.
        strategy: Relaxation strategy name.
        
    Returns:
        The updated query dictionary.
    """
    if isinstance(parsed_query_json, str):
        try:
            query = json.loads(parsed_query_json)
        except Exception:
            query = {}
    else:
        query = dict(parsed_query_json)
        
    strategy = str(strategy).lower()
    
    if "remove_color_and_material" in strategy:
        query["color"] = None
        query["material"] = None
    elif "remove_color" in strategy:
        query["color"] = None
    elif "remove_material" in strategy:
        query["material"] = None
    elif "increase_price_ceiling" in strategy or "price" in strategy:
        max_p = query.get("max_price")
        if max_p is not None:
            try:
                query["max_price"] = float(max_p) * 1.2
            except (ValueError, TypeError):
                pass
    elif "make_size_optional" in strategy or "size" in strategy:
        query["generic_size"] = None
        
    return query
