import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from main import app

client = TestClient(app)

@pytest.fixture
def mock_graph_result():
    return {
        "ranked_products": [
            {
                "id": "outfitters_1",
                "store_name": "Outfitters",
                "store_slug": "outfitters",
                "title": "Mustard Lawn Kurta",
                "price": 2500.0,
                "compare_price": 3000.0,
                "currency": "PKR",
                "available_sizes": ["S", "M", "L"],
                "matched_size": "M",
                "image_url": "https://example.com/img.jpg",
                "product_url": "https://outfitters.com.pk/products/yellow-kurta",
                "tags": ["lawn", "yellow"],
                "relevance_score": 0.95
            }
        ],
        "failed_stores": ["limelight"],
        "stores_queried": 2,
        "stores_responded": 1,
        "parsed_query": {
            "item_type": "kurta",
            "color": "mustard",
            "gender": "women"
        },
        "search_summary": "Found 1 mustard lawn kurta at Outfitters.",
        "retrieval_iterations": 1
    }

@patch("routers.search.fashion_graph.ainvoke")
def test_search_text_success(mock_ainvoke, mock_graph_result):
    mock_ainvoke.return_value = mock_graph_result
    
    response = client.post(
        "/api/search/text",
        data={"query": "mustard kurta", "measurements_json": '{"chest": 35.5}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "outfitters_1"
    assert data["query_parsed"]["color"] == "mustard"
    assert data["search_summary"] == "Found 1 mustard lawn kurta at Outfitters."
    assert data["failed_stores"] == ["limelight"]

@patch("routers.search.fashion_graph.ainvoke")
def test_search_text_invalid_measurements(mock_ainvoke):
    response = client.post(
        "/api/search/text",
        data={"query": "mustard kurta", "measurements_json": "invalid-json"}
    )
    assert response.status_code == 400
    assert "Invalid measurements_json" in response.json()["detail"]

@patch("routers.search.fashion_graph.ainvoke")
def test_search_visual_success(mock_ainvoke, mock_graph_result):
    mock_ainvoke.return_value = mock_graph_result
    
    # Mock visual search with a mock image file
    file_content = b"fake-image-bytes"
    files = {"image": ("test.jpg", file_content, "image/jpeg")}
    
    response = client.post(
        "/api/search/visual",
        files=files,
        data={"measurements_json": '{"chest": 35.5}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "outfitters_1"

@patch("routers.search.fashion_graph.ainvoke")
def test_search_visual_invalid_file_type(mock_ainvoke):
    # Upload text file instead of image
    files = {"image": ("test.txt", b"plain text", "text/plain")}
    
    response = client.post(
        "/api/search/visual",
        files=files
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

@patch("routers.search.fashion_graph.ainvoke")
def test_search_visual_file_too_large(mock_ainvoke):
    # Upload file larger than 5MB
    large_content = b"a" * (5 * 1024 * 1024 + 1)
    files = {"image": ("test.jpg", large_content, "image/jpeg")}
    
    response = client.post(
        "/api/search/visual",
        files=files
    )
    assert response.status_code == 400
    assert "Image size exceeds the 5MB limit" in response.json()["detail"]
