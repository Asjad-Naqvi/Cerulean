import os
import json
import asyncio
from typing import Dict, Any, List
import google.generativeai as genai

from agents.state import AgentState
from tools.query_tools import parse_text_query_fn, parse_image_query_fn
from tools.store_tools import select_target_stores_fn, ACTIVE_STORES

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=api_key)

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent for a Pakistani Live Fashion Aggregator search engine.
Your task is to analyze the user's search intent and plan the search.

Follow this workflow:
1. Parse the user's input.
   - If the user provides a text query, call `parse_text_query_fn`.
   - If the user provides an image query, call `parse_image_query_fn`.
2. Select target stores.
   - Using the parsed query's price_tier, gender, and categories, call `select_target_stores_fn` to choose which stores to query.

You must run these tools to output structured data. Do not output conversational text until you have called both tools.
"""

TOOL_DISPATCH = {
    "parse_text_query_fn": parse_text_query_fn,
    "parse_image_query_fn": parse_image_query_fn,
    "select_target_stores_fn": select_target_stores_fn
}

async def planner_node(state: AgentState) -> AgentState:
    print(f"DEBUG: [planner_node] Starting planner node with raw_query={state.get('raw_query')}", flush=True)
    parsed_query = None
    target_store_slugs = None
    
    raw_query = state.get("raw_query")
    image_bytes = state.get("image_bytes")
    image_mime_type = state.get("image_mime_type")
    
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        tools=[parse_text_query_fn, parse_image_query_fn, select_target_stores_fn],
        system_instruction=PLANNER_SYSTEM_PROMPT
    )
    
    user_parts = []
    if image_bytes:
        user_parts.append({
            "mime_type": image_mime_type or "image/jpeg",
            "data": image_bytes
        })
        user_parts.append("User uploaded an image. Extract search parameters from this image and select target stores.")
    else:
        user_parts.append(f"User query: {raw_query or ''}")
        
    messages = [{"role": "user", "parts": user_parts}]
    
    for i in range(5):
        print(f"DEBUG: [planner_node] Iteration {i+1}: Calling generate_content_async...", flush=True)
        response = await model.generate_content_async(
            contents=messages
        )
        print(f"DEBUG: [planner_node] Iteration {i+1}: Received response.", flush=True)
        
        if not response.candidates:
            break
            
        model_content = response.candidates[0].content
        messages.append(model_content)
        
        function_calls = [part.function_call for part in model_content.parts if part.function_call]
        if function_calls:
            print(f"DEBUG: [planner_node] Iteration {i+1}: Found function calls: {[fc.name for fc in function_calls]}", flush=True)
        else:
            break
            
        tool_response_parts = []
        for fc in function_calls:
            tool_name = fc.name
            tool_args = dict(fc.args)
            print(f"DEBUG: [planner_node] Executing tool: {tool_name} with args: {tool_args}", flush=True)
            
            try:
                tool_func = TOOL_DISPATCH.get(tool_name)
                if tool_func:
                    result = tool_func(**tool_args)
                else:
                    result = {"error": f"Tool '{tool_name}' not found"}
            except Exception as e:
                result = {"error": str(e)}
                
            if tool_name in ("parse_text_query_fn", "parse_image_query_fn") and "error" not in result:
                parsed_query = result
            elif tool_name == "select_target_stores_fn" and "error" not in result:
                target_store_slugs = result
                
            resp_part = {
                "function_response": {
                    "name": tool_name,
                    "response": {"result": result}
                }
            }
            tool_response_parts.append(resp_part)
            
        messages.append({"role": "user", "parts": tool_response_parts})
        
        # Break early once we have both target stores and the parsed query
        if parsed_query is not None and target_store_slugs is not None:
            break

    if parsed_query is None:
        parsed_query = {
            "item_type": "clothing",
            "color": None,
            "material": None,
            "gender": "any",
            "price_tier": "any",
            "style_category": None,
            "min_price": None,
            "max_price": None,
            "generic_size": None,
            "occasion": None
        }
        
    gender_constraint = state.get("gender_constraint")
    if gender_constraint and gender_constraint != "any":
        parsed_query["gender"] = gender_constraint

    if target_store_slugs is None:
        target_store_slugs = select_target_stores_fn(
            price_tier=parsed_query.get("price_tier", "any"),
            gender=parsed_query.get("gender", "any")
        )
        
    hint_parts = []
    if parsed_query.get("color"):
        hint_parts.append(parsed_query["color"])
    if parsed_query.get("material"):
        hint_parts.append(parsed_query["material"])
    if parsed_query.get("item_type"):
        hint_parts.append(parsed_query["item_type"])
        
    search_hint = " ".join(hint_parts) if hint_parts else "kurta"

    return {
        **state,
        "parsed_query": parsed_query,
        "target_store_slugs": target_store_slugs,
        "search_hint": search_hint,
        "retrieval_iterations": 0
    }
