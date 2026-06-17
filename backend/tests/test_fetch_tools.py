import pytest
import respx
import httpx
from tools.fetch_tools import fetch_store_fn, STORE_MAP

@pytest.mark.asyncio
@respx.mock
async def test_fetch_store_shopify_success():
    # Setup mock shopify store
    slug = "outfitters"
    store = STORE_MAP[slug]
    base_url = store["base_url"]
    endpoint = store["products_endpoint"]
    
    mock_payload = {
        "products": [
            {
                "id": 12345,
                "title": "Stunning Kurta",
                "handle": "stunning-kurta",
                "tags": "lawn, summer",
                "images": [{"src": "https://example.com/img.jpg"}],
                "variants": [
                    {
                        "id": 99999,
                        "title": "S",
                        "price": "2500.00",
                        "compare_at_price": "3000.00",
                        "available": True,
                        "option1": "S"
                    }
                ],
                "options": [{"name": "Size"}]
            }
        ]
    }
    
    respx.get(f"{base_url}{endpoint}").mock(return_value=httpx.Response(200, json=mock_payload))
    
    res = await fetch_store_fn(slug, "kurta")
    assert res["success"] is True
    assert res["slug"] == slug
    products = res["products"]
    assert len(products) == 1
    prod = products[0]
    assert prod["id"] == f"{slug}_12345"
    assert prod["title"] == "Stunning Kurta"
    assert prod["price"] == 2500.0
    assert prod["compare_price"] == 3000.0
    assert prod["image_url"] == "https://example.com/img.jpg"
    assert "S" in prod["available_sizes"]

@pytest.mark.asyncio
@respx.mock
async def test_fetch_store_woo_success():
    # Inject a mock woo store into STORE_MAP
    slug = "mock_woo"
    STORE_MAP[slug] = {
        "slug": slug,
        "name": "Mock Woo Store",
        "base_url": "https://mockwoo.com",
        "platform": "woocommerce",
        "products_endpoint": "/wp-json/wc/store/v1/products",
        "price_tier": "mid",
        "gender": "women",
        "categories": ["clothing"]
    }
    
    store = STORE_MAP[slug]
    base_url = store["base_url"]
    endpoint = store["products_endpoint"]
    
    mock_payload = [
        {
            "id": 67890,
            "name": "Floral Frock",
            "permalink": "https://example.com/floral-frock",
            "tags": [{"name": "floral"}, {"name": "cotton"}],
            "images": [{"src": "https://example.com/frock.jpg"}],
            "prices": {
                "price": "350000",  # minor units -> 3500.0
                "regular_price": "400000"
            },
            "stock_status": "instock",
            "variations": [
                {
                    "in_stock": True,
                    "attributes": [{"name": "Size", "value": "M"}]
                }
            ]
        }
    ]
    
    respx.get(f"{base_url}{endpoint}").mock(return_value=httpx.Response(200, json=mock_payload))
    
    res = await fetch_store_fn(slug, "frock")
    assert res["success"] is True
    products = res["products"]
    assert len(products) == 1
    prod = products[0]
    assert prod["id"] == f"{slug}_67890"
    assert prod["price"] == 3500.0
    assert prod["compare_price"] == 4000.0
    assert "M" in prod["available_sizes"]

@pytest.mark.asyncio
@respx.mock
async def test_fetch_store_http_error():
    slug = "outfitters"
    store = STORE_MAP[slug]
    base_url = store["base_url"]
    endpoint = store["products_endpoint"]
    
    respx.get(f"{base_url}{endpoint}").mock(return_value=httpx.Response(500))
    
    res = await fetch_store_fn(slug)
    assert res["success"] is False
    assert "HTTP 500" in res["error"]

@pytest.mark.asyncio
@respx.mock
async def test_fetch_store_network_failure():
    slug = "outfitters"
    store = STORE_MAP[slug]
    base_url = store["base_url"]
    endpoint = store["products_endpoint"]
    
    respx.get(f"{base_url}{endpoint}").mock(side_effect=httpx.ConnectError("Network is down"))
    
    res = await fetch_store_fn(slug)
    assert res["success"] is False
    assert "Network is down" in res["error"]
