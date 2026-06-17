import pytest
import json
from tools.size_tools import map_product_sizes_fn, broaden_search_criteria_fn, _resolve_size

@pytest.fixture
def sample_products():
    return [
        {
            "id": "outfitters_1",
            "store_name": "Outfitters",
            "store_slug": "outfitters",
            "title": "Mustard Lawn Kurta",
            "price": 2500.0,
            "compare_price": 3000.0,
            "currency": "PKR",
            "available_sizes": ["S", "M", "L"],
            "tags": ["lawn", "mustard", "kurta"]
        },
        {
            "id": "generation_1",
            "store_name": "Generation",
            "store_slug": "generation",
            "title": "Blue Cotton Shirt",
            "price": 4000.0,
            "compare_price": None,
            "currency": "PKR",
            "available_sizes": ["M", "L", "XL"],
            "tags": ["cotton", "blue", "shirt"]
        }
    ]

def test_resolve_size():
    # Outfitters: XS=33, S=35, M=37, L=39, XL=41
    assert _resolve_size("outfitters", 34.0) == "S"
    assert _resolve_size("outfitters", 36.5) == "M"
    assert _resolve_size("outfitters", 37.0) == "M"
    assert _resolve_size("outfitters", 45.0) is None

def test_map_product_sizes_generic_size(sample_products):
    # If generic size is L, it should return products where L is available
    res = map_product_sizes_fn(sample_products, generic_size="L")
    products = res["products"]
    assert len(products) == 2
    assert products[0]["matched_size"] == "L"
    assert products[1]["matched_size"] == "L"

    # If generic size is XS, it should drop products that don't have XS available
    res = map_product_sizes_fn(sample_products, generic_size="XS")
    products = res["products"]
    assert len(products) == 0

def test_map_product_sizes_measurements(sample_products):
    # Chest 35.5 should map to M for Outfitters (has S,M,L -> M fits and is available)
    # Chest 35.5 should map to M for Generation (has M,L,XL -> M fits and is available)
    res = map_product_sizes_fn(sample_products, measurements_json={"chest": 35.5})
    products = res["products"]
    assert len(products) == 2
    assert products[0]["matched_size"] == "M"
    assert products[1]["matched_size"] == "M"

def test_broaden_search_criteria():
    query = {"color": "mustard", "material": "lawn", "max_price": 3000, "generic_size": "M"}
    
    # remove_color
    res = broaden_search_criteria_fn(query, "remove_color")
    assert res["color"] is None
    assert res["material"] == "lawn"

    # remove_color_and_material
    res = broaden_search_criteria_fn(query, "remove_color_and_material")
    assert res["color"] is None
    assert res["material"] is None

    # price increase
    res = broaden_search_criteria_fn(query, "increase_price_ceiling_20pct")
    assert res["max_price"] == 3600.0

    # make_size_optional
    res = broaden_search_criteria_fn(query, "make_size_optional")
    assert res["generic_size"] is None
