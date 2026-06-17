import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from models.schemas import Product
from tools.store_tools import ACTIVE_STORES

STORE_MAP = {s["slug"]: s for s in ACTIVE_STORES}
STORE_TIMEOUT = float(os.getenv("STORE_TIMEOUT", 2.5))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (FashionAggregator/1.0)"

def _normalize_shopify(store_slug: str, store_name: str, raw_prod: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        prod_id = str(raw_prod.get("id", ""))
        title = raw_prod.get("title", "")
        
        # Build product URL
        handle = raw_prod.get("handle", "")
        base_url = STORE_MAP[store_slug]["base_url"]
        product_url = f"{base_url}/products/{handle}"
        
        # Images
        image_url = None
        images = raw_prod.get("images", [])
        if images and isinstance(images, list):
            image_url = images[0].get("src")
        elif raw_prod.get("image"):
            image_url = raw_prod.get("image", {}).get("src")

        # Tags
        tags_raw = raw_prod.get("tags", "")
        if isinstance(tags_raw, str):
            tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
        elif isinstance(tags_raw, list):
            tags = [str(t).strip().lower() for t in tags_raw]
        else:
            tags = []
            
        # Add title keywords to tags for easier matching
        tags.extend([t.lower() for t in title.split() if len(t) > 2])

        # Sizing and pricing from variants
        variants = raw_prod.get("variants", [])
        if not variants:
            return None

        # Find option corresponding to size
        size_option_idx = 0
        options = raw_prod.get("options", [])
        for i, opt in enumerate(options):
            if "size" in opt.get("name", "").lower():
                size_option_idx = i
                break
        
        option_keys = ["option1", "option2", "option3"]
        size_key = option_keys[size_option_idx] if size_option_idx < len(option_keys) else "option1"

        available_sizes = []
        in_stock_variants = []
        for var in variants:
            if var.get("available", False):
                # Extract size label
                size_label = var.get(size_key) or var.get("title") or ""
                size_label = size_label.strip().upper()
                if size_label and size_label not in available_sizes:
                    available_sizes.append(size_label)
                in_stock_variants.append(var)

        # If no variants are in stock, we skip this product
        if not in_stock_variants:
            return None

        # Price info from the first in-stock variant
        ref_variant = in_stock_variants[0]
        
        def safe_float(val) -> Optional[float]:
            if val is None or val == "":
                return None
            try:
                return float(val)
            except ValueError:
                return None

        price = safe_float(ref_variant.get("price"))
        if price is None:
            return None
            
        compare_price = safe_float(ref_variant.get("compare_at_price"))
        # If compare price is same or lower, set to None
        if compare_price is not None and compare_price <= price:
            compare_price = None

        return {
            "id": f"{store_slug}_{prod_id}",
            "store_name": store_name,
            "store_slug": store_slug,
            "title": title,
            "price": price,
            "compare_price": compare_price,
            "currency": "PKR",
            "available_sizes": available_sizes,
            "matched_size": None,
            "image_url": image_url,
            "product_url": product_url,
            "tags": list(set(tags)),
            "relevance_score": None
        }
    except Exception:
        return None

def _normalize_woocommerce(store_slug: str, store_name: str, raw_prod: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        prod_id = str(raw_prod.get("id", ""))
        title = raw_prod.get("name", "")
        product_url = raw_prod.get("permalink", "")
        
        # Images
        image_url = None
        images = raw_prod.get("images", [])
        if images and isinstance(images, list):
            image_url = images[0].get("src")

        # Tags
        tags = []
        for tag_obj in raw_prod.get("tags", []):
            if isinstance(tag_obj, dict) and "name" in tag_obj:
                tags.append(tag_obj["name"].lower())
        tags.extend([t.lower() for t in title.split() if len(t) > 2])

        # Price info
        prices = raw_prod.get("prices", {})
        
        def woo_price_to_float(val) -> Optional[float]:
            if val is None or val == "":
                return None
            try:
                # Woo API minor units -> divide by 100
                return float(val) / 100.0
            except ValueError:
                return None

        price = woo_price_to_float(prices.get("price"))
        if price is None:
            return None
            
        compare_price = woo_price_to_float(prices.get("regular_price"))
        if compare_price is not None and compare_price <= price:
            compare_price = None

        # Sizing and availability from variations
        available_sizes = []
        variations = raw_prod.get("variations", [])
        
        if variations:
            for var in variations:
                if var.get("in_stock", True):
                    # Check for size attribute
                    attributes = var.get("attributes", [])
                    size_val = None
                    for attr in attributes:
                        if "size" in attr.get("name", "").lower():
                            size_val = attr.get("value", "")
                            break
                    if not size_val and attributes:
                        size_val = attributes[0].get("value", "")
                    
                    if size_val:
                        size_val = size_val.strip().upper()
                        if size_val not in available_sizes:
                            available_sizes.append(size_val)
        else:
            # Simple product, check if in stock
            if raw_prod.get("stock_status", "instock") == "instock":
                # Get sizes from main attributes
                attributes = raw_prod.get("attributes", [])
                for attr in attributes:
                    if "size" in attr.get("name", "").lower():
                        terms = attr.get("terms", [])
                        for term in terms:
                            if isinstance(term, dict) and "name" in term:
                                available_sizes.append(term["name"].strip().upper())
                            elif isinstance(term, str):
                                available_sizes.append(term.strip().upper())

        # If the product isn't in stock or has no sizes, we skip it
        if not available_sizes:
            return None

        return {
            "id": f"{store_slug}_{prod_id}",
            "store_name": store_name,
            "store_slug": store_slug,
            "title": title,
            "price": price,
            "compare_price": compare_price,
            "currency": "PKR",
            "available_sizes": available_sizes,
            "matched_size": None,
            "image_url": image_url,
            "product_url": product_url,
            "tags": list(set(tags)),
            "relevance_score": None
        }
    except Exception:
        return None

async def fetch_store_fn(slug: str, search_hint: str = "") -> Dict[str, Any]:
    """
    Fetches and normalizes products from a single store.
    
    Args:
        slug: The store slug to check.
        search_hint: Optional query keyword (e.g. 'kurta') to pass as search param.
        
    Returns:
        Dict containing success flag, store slug, and products list or error string.
    """
    store = STORE_MAP.get(slug)
    if not store:
        return {"success": False, "slug": slug, "error": "Store not found or inactive"}

    base_url = store["base_url"]
    platform = store["platform"]
    endpoint = store["products_endpoint"]
    
    url = f"{base_url}{endpoint}"
    params = {}
    
    if platform == "shopify":
        params["limit"] = 100
        if search_hint:
            params["title"] = search_hint
    else:  # woocommerce
        params["per_page"] = 50
        if search_hint:
            params["search"] = search_hint

    headers = {"User-Agent": USER_AGENT}
    
    try:
        async with httpx.AsyncClient(headers=headers, verify=False) as client:
            response = await client.get(url, params=params, timeout=STORE_TIMEOUT, follow_redirects=True)
            
            if response.status_code != 200:
                return {"success": False, "slug": slug, "error": f"HTTP {response.status_code}"}
                
            data = response.json()
            products_list = []
            
            if platform == "shopify":
                raw_products = data.get("products", [])
                for rp in raw_products:
                    norm = _normalize_shopify(slug, store["name"], rp)
                    if norm:
                        products_list.append(norm)
            else:  # woocommerce
                raw_products = data if isinstance(data, list) else []
                for rp in raw_products:
                    norm = _normalize_woocommerce(slug, store["name"], rp)
                    if norm:
                        products_list.append(norm)
                        
            return {"success": True, "slug": slug, "products": products_list}
            
    except Exception as e:
        return {"success": False, "slug": slug, "error": str(e)}
