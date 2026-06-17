import os
import json
import re
import asyncio
from typing import Dict, Any, List
import google.generativeai as genai

from agents.state import AgentState

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=api_key)

RANKER_SYSTEM_PROMPT = """You are the Ranker Agent for a Pakistani Live Fashion Aggregator search engine.
Your task is to re-rank the filtered search results based on semantic relevance to the user's original query.

Consider:
- Color accuracy (e.g., matching 'mustard' vs generic 'yellow').
- Fabric correctness (e.g., 'lawn', 'linen', 'cotton').
- Category/Style matching (e.g., 'kurta', 'frock').
- Occasion relevance (e.g., 'casual', 'formal').

For each product, assign a 'relevance_score' float between 0.0 and 1.0.
Sort the final list in descending order of 'relevance_score'.

Additionally, write a brief 'search_summary' (maximum 20 words) explaining what was found (e.g. "Found 12 mustard lawn kurtas across 7 stores, ₨2,800–₨8,500.").

You must output ONLY a valid JSON object matching the schema below. Do NOT wrap it in markdown blocks or include any other text.
Schema:
{
  "ranked_products": [
    {
      "id": "string",
      "store_name": "string",
      "store_slug": "string",
      "title": "string",
      "price": 0.0,
      "compare_price": 0.0,
      "currency": "PKR",
      "available_sizes": ["S", "M"],
      "matched_size": "M",
      "image_url": "string",
      "product_url": "string",
      "tags": ["string"],
      "relevance_score": 0.95
    }
  ],
  "search_summary": "string"
}
"""

def _clean_json(text: str) -> str:
    cleaned = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()

async def ranker_node(state: AgentState) -> AgentState:
    filtered = state.get("filtered_products", [])
    raw_query = state.get("raw_query") or "image search"
    parsed_query = state.get("parsed_query") or {}
    
    if not filtered:
        return {
            **state,
            "ranked_products": [],
            "search_summary": "No matching products were found. Try modifying your search criteria."
        }

    prompt = (
        f"Original User Query: {raw_query}\n"
        f"Parsed Intent: {parsed_query}\n"
        f"Products to Re-Rank (JSON):\n{json.dumps(filtered, indent=2)}"
    )

    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        system_instruction=RANKER_SYSTEM_PROMPT
    )

    try:
        response = await model.generate_content_async(
            contents=prompt,
            generation_config={
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        )
        
        raw_text = response.text if response.text else "{}"
        cleaned_text = _clean_json(raw_text)
        data = json.loads(cleaned_text)
        
        ranked_products = data.get("ranked_products", [])
        search_summary = data.get("search_summary", "")
        
        if not isinstance(ranked_products, list) or not search_summary:
            raise ValueError("Invalid JSON fields")
            
    except Exception as e:
        import traceback
        print("DEBUG: [ranker_node] Exception in ranker node:", e)
        traceback.print_exc()
        # Fallback to price-sorted list with default summary and no scores
        ranked_products = []
        for p in filtered:
            p_copy = dict(p)
            p_copy["relevance_score"] = 1.0
            ranked_products.append(p_copy)
            
        prices = [p.get("price", 0.0) for p in filtered if p.get("price") is not None]
        min_p = int(min(prices)) if prices else 0
        max_p = int(max(prices)) if prices else 0
        unique_stores = len(set(p.get("store_name") for p in filtered))
        search_summary = f"Found {len(filtered)} items across {unique_stores} stores, PKR {min_p:,}–PKR {max_p:,}."
        
    return {
        **state,
        "ranked_products": ranked_products,
        "search_summary": search_summary
    }
