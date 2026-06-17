import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.graph import fashion_graph

# Mock structures for Gemini responses
class MockFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class MockPart:
    def __init__(self, name=None, args=None, text=None):
        if name:
            self.function_call = MockFunctionCall(name, args)
            self.text = None
        else:
            self.function_call = None
            self.text = text

class MockContent:
    def __init__(self, parts):
        self.parts = parts

class MockCandidate:
    def __init__(self, parts):
        self.content = MockContent(parts)

class MockResponse:
    def __init__(self, parts, text="{}"):
        self.candidates = [MockCandidate(parts)]
        self.text = text

@pytest.mark.asyncio
@patch("google.generativeai.GenerativeModel")
@patch("agents.retrieval_agent.fetch_store_fn")
async def test_graph_smoke_run(mock_fetch, mock_model_class):
    # Set up mock fetch
    mock_fetch.return_value = {
        "success": True,
        "slug": "outfitters",
        "products": [
            {
                "id": f"outfitters_{i}",
                "store_name": "Outfitters",
                "store_slug": "outfitters",
                "title": "Yellow Printed Kurta",
                "price": 2500.0,
                "compare_price": None,
                "currency": "PKR",
                "available_sizes": ["S", "M", "L"],
                "matched_size": None,
                "image_url": "https://example.com/img.jpg",
                "product_url": "https://outfitters.com.pk/products/yellow-printed-kurta",
                "tags": ["lawn", "yellow", "kurta"],
                "relevance_score": None
            } for i in range(5)
        ]
    }
    
    # Configure mock Gemini model responses
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    
    # Setup call sequences for generate_content_async (which is an async method)
    # Turn 1 (Planner): Call parse_text_query_fn and select_target_stores_fn
    planner_resp_1 = MockResponse([
        MockPart(name="parse_text_query_fn", args={"item_type": "kurta", "color": "yellow"}),
        MockPart(name="select_target_stores_fn", args={"price_tier": "mid"})
    ])
    # Turn 2 (Planner Loop End): No function calls
    planner_resp_2 = MockResponse([])
    
    # Turn 3 (Retrieval): Call fetch_store_fn
    retrieval_resp_1 = MockResponse([
        MockPart(name="fetch_store_fn", args={"slug": "outfitters", "search_hint": "yellow kurta"})
    ])
    # Turn 4 (Retrieval Loop End): No function calls
    retrieval_resp_2 = MockResponse([])
    
    # Turn 5 (Ranker): Returns ranked output JSON
    ranker_json = '{"ranked_products": [{"id": "outfitters_1", "store_name": "Outfitters", "store_slug": "outfitters", "title": "Yellow Printed Kurta", "price": 2500.0, "compare_price": null, "currency": "PKR", "available_sizes": ["S", "M", "L"], "matched_size": "M", "image_url": "https://example.com/img.jpg", "product_url": "https://outfitters.com.pk/products/yellow-printed-kurta", "tags": ["lawn", "yellow", "kurta"], "relevance_score": 0.95}], "search_summary": "Found 1 yellow kurta at Outfitters."}'
    ranker_resp = MockResponse([], text=ranker_json)
    
    # Chain the mock responses for generate_content_async calls (which is an AsyncMock)
    mock_model.generate_content_async = AsyncMock()
    mock_model.generate_content_async.side_effect = [
        planner_resp_1, planner_resp_2,
        retrieval_resp_1, retrieval_resp_2,
        ranker_resp
    ]
    
    initial_state = {
        "raw_query": "yellow kurta",
        "image_bytes": None,
        "image_mime_type": None,
        "measurements": {"chest": 36.0},
        "parsed_query": None,
        "target_store_slugs": None,
        "search_hint": None,
        "filtered_products": None,
        "failed_stores": [],
        "stores_queried": 0,
        "stores_responded": 0,
        "retrieval_iterations": 0,
        "ranked_products": None,
        "search_summary": None
    }
    
    result = await fashion_graph.ainvoke(initial_state)
    
    assert result is not None
    assert result["parsed_query"] is not None
    assert result["parsed_query"]["item_type"] == "kurta"
    assert "outfitters" in result["target_store_slugs"]
    assert len(result["ranked_products"]) == 1
    assert result["ranked_products"][0]["relevance_score"] == 0.95
    assert "yellow" in result["search_summary"]
