import os
import httpx
import json
from typing import Optional
from fastapi import APIRouter, Form, File, UploadFile, HTTPException

from models.schemas import SearchResponse
from agents.graph import fashion_graph

from openai import AsyncOpenAI

router = APIRouter()

async def generate_style_concept(query_desc: str) -> Optional[str]:
    api_key = os.getenv("TOGETHER_API_KEY", "")
    if not api_key:
        return None
        
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.together.xyz/v1"
        )
        response = await client.images.generate(
            prompt=f"Professional fashion photography of a model wearing a modern Pakistani style {query_desc}, clean studio background, highly detailed, premium look",
            model="black-forest-labs/FLUX.1-schnell",
            response_format="b64_json"
        )
        b64 = response.data[0].b64_json
        if b64:
            return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"DEBUG: [generate_style_concept] Image generation failed: {e}", flush=True)
        
    return None

async def _run_graph(state: dict) -> dict:
    try:
        final_state = await fashion_graph.ainvoke(state)
        
        # Determine prompt description
        query_parsed = final_state.get("parsed_query") or {}
        hint_parts = []
        if query_parsed.get("color"):
            hint_parts.append(query_parsed["color"])
        if query_parsed.get("material"):
            hint_parts.append(query_parsed["material"])
        if query_parsed.get("item_type"):
            hint_parts.append(query_parsed["item_type"])
        query_desc = " ".join(hint_parts) if hint_parts else (state.get("raw_query") or "fashion clothing")
        
        # Generate style concept image using Together AI FLUX image model
        style_img = await generate_style_concept(query_desc)
        
        return {
            "results": final_state.get("ranked_products") or [],
            "total_count": len(final_state.get("ranked_products") or []),
            "stores_queried": final_state.get("stores_queried", 0),
            "stores_responded": final_state.get("stores_responded", 0),
            "failed_stores": final_state.get("failed_stores") or [],
            "query_parsed": query_parsed,
            "search_summary": final_state.get("search_summary", ""),
            "retrieval_iterations": final_state.get("retrieval_iterations", 0),
            "style_concept_image": style_img
        }
    except Exception as e:
        # Wrap graph execution errors in 503 HTTP exception
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: Graph execution failed. Details: {str(e)}"
        )

@router.post("/search/text", response_model=SearchResponse)
async def search_text(
    query: str = Form(...),
    measurements_json: Optional[str] = Form(None),
    gender: Optional[str] = Form(None)
):
    measurements = None
    if measurements_json:
        try:
            measurements = json.loads(measurements_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid measurements_json format")

    initial_state = {
        "raw_query": query,
        "image_bytes": None,
        "image_mime_type": None,
        "measurements": measurements,
        "gender_constraint": gender or "any",
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
    
    return await _run_graph(initial_state)

@router.post("/search/visual", response_model=SearchResponse)
async def search_visual(
    image: UploadFile = File(...),
    measurements_json: Optional[str] = Form(None),
    gender: Optional[str] = Form(None)
):
    # Validate MIME type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    # Read bytes and validate file size (limit: 5MB)
    contents = await image.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds the 5MB limit")

    measurements = None
    if measurements_json:
        try:
            measurements = json.loads(measurements_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid measurements_json format")

    initial_state = {
        "raw_query": None,
        "image_bytes": contents,
        "image_mime_type": image.content_type,
        "measurements": measurements,
        "gender_constraint": gender or "any",
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
    
    return await _run_graph(initial_state)
