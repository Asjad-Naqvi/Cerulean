import pytest
import json
from tools.filter_tools import filter_products_fn

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
            "id": "sapphire_1",
            "store_name": "Sapphire",
            "store_slug": "sapphirepk",
            "title": "Blue Cotton Shirt",
            "price": 4000.0,
            "compare_price": None,
            "currency": "PKR",
            "available_sizes": ["M", "L", "XL"],
            "tags": ["cotton", "blue", "shirt"]
        },
        {
            "id": "limelight_1",
            "store_name": "Limelight",
            "store_slug": "limelight",
            "title": "Red Linen Kurta",
            "price": 1800.0,
            "compare_price": 2000.0,
            "currency": "PKR",
            "available_sizes": ["XS", "S"],
            "tags": ["linen", "red", "kurta"]
        }
    ]

def test_filter_products_by_item_type(sample_products):
    query = {"item_type": "kurta"}
    res = filter_products_fn(sample_products, query)
    products = res["products"]
    assert len(products) == 2
    # Verify price sorted (1800 < 2500)
    assert products[0]["id"] == "limelight_1"
    assert products[1]["id"] == "outfitters_1"

def test_filter_products_by_color(sample_products):
    query = {"color": "blue"}
    res = filter_products_fn(sample_products, query)
    products = res["products"]
    assert len(products) == 1
    assert products[0]["id"] == "sapphire_1"

def test_filter_products_by_price_range(sample_products):
    query = {"min_price": 2000, "max_price": 3000}
    res = filter_products_fn(sample_products, query)
    products = res["products"]
    assert len(products) == 1
    assert products[0]["id"] == "outfitters_1"

def test_filter_products_json_string_input(sample_products):
    products_str = json.dumps(sample_products)
    query_str = json.dumps({"item_type": "kurta", "color": "red"})
    res = filter_products_fn(products_str, query_str)
    products = res["products"]
    assert len(products) == 1
    assert products[0]["id"] == "limelight_1"
