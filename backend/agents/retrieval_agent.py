import os
import json
import asyncio
from typing import Dict, Any, List
import google.generativeai as genai

from agents.state import AgentState
from tools.fetch_tools import fetch_store_fn
from tools.filter_tools import filter_products_fn
from tools.size_tools import map_product_sizes_fn, broaden_search_criteria_fn

MAX_ITERATIONS = 2
SPARSE_THRESHOLD = 5

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=api_key)

RETRIEVAL_SYSTEM_PROMPT = """You are the Retrieval Agent for a Pakistani Live Fashion Aggregator search engine.
Your task is to fetch products from selected stores, filter them, and map their sizes.

Follow this sequence of actions:
1. Fetch products from ALL target stores concurrently by calling `fetch_store_fn` for each store slug.
2. Accumulate the products returned by all stores.
3. Filter the accumulated products using `filter_products_fn`.
4. Map sizes of the filtered products using `map_product_sizes_fn`.
5. Check if the final product count is at least 5. If it is less than 5 and you have not reached the max iteration count (MAX_ITERATIONS=2), call `broaden_search_criteria_fn` to relax the query, and repeat the retrieval process with the new query.

Always output the results of these tool calls.
"""

TOOL_DISPATCH = {
    "fetch_store_fn": fetch_store_fn,
    "filter_products_fn": filter_products_fn,
    "map_product_sizes_fn": map_product_sizes_fn,
    "broaden_search_criteria_fn": broaden_search_criteria_fn
}

async def retrieval_node(state: AgentState) -> AgentState:
    target_stores = state.get("target_store_slugs", [])
    parsed_query = state.get("parsed_query", {})
    search_hint = state.get("search_hint", "")
    measurements = state.get("measurements")
    generic_size = parsed_query.get("generic_size") if parsed_query else None
    
    current_iteration = state.get("retrieval_iterations", 0)
    
    # State accumulators for this run
    raw_products_accumulated = []
    failed_stores = list(state.get("failed_stores", []))
    stores_queried = state.get("stores_queried", 0)
    stores_responded = state.get("stores_responded", 0)
    filtered_products = list(state.get("filtered_products", [])) if state.get("filtered_products") else []

    user_instruction = (
        f"Target stores to query: {target_stores}. "
        f"Search query: {parsed_query}. "
        f"Search hint: '{search_hint}'. "
        f"User measurements: {measurements}. "
        f"Current iteration: {current_iteration}."
    )
    
    messages = [
        {"role": "user", "parts": [
            f"System Instruction: {RETRIEVAL_SYSTEM_PROMPT}\n\nUser input: {user_instruction}"
        ]}
    ]
    
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        tools=[fetch_store_fn, filter_products_fn, map_product_sizes_fn, broaden_search_criteria_fn]
    )

    print(f"DEBUG: [retrieval_node] Starting retrieval node with target_stores={target_stores}", flush=True)

    for i in range(5):
        print(f"DEBUG: [retrieval_node] Iteration {i+1}: Calling generate_content_async...", flush=True)
        response = await model.generate_content_async(
            contents=messages
        )
        print(f"DEBUG: [retrieval_node] Iteration {i+1}: Received response.", flush=True)
        
        if not response.candidates:
            break
            
        model_content = response.candidates[0].content
        messages.append(model_content)
        
        function_calls = [part.function_call for part in model_content.parts if part.function_call]
        if function_calls:
            print(f"DEBUG: [retrieval_node] Iteration {i+1}: Found function calls: {[fc.name for fc in function_calls]}", flush=True)
        else:
            break

        # Separate fetch calls from other calls for concurrent execution
        fetch_calls = []
        other_calls = []
        for fc in function_calls:
            if fc.name == "fetch_store_fn":
                fetch_calls.append(fc)
            else:
                other_calls.append(fc)

        # Run fetches concurrently using gather
        fetch_results = []
        if fetch_calls:
            tasks = []
            for fc in fetch_calls:
                slug = fc.args.get("slug")
                hint = fc.args.get("search_hint") or search_hint
                print(f"DEBUG: [retrieval_node] Queueing fetch_store_fn for slug={slug} with hint={hint}", flush=True)
                tasks.append(fetch_store_fn(slug, hint))
            print(f"DEBUG: [retrieval_node] Executing {len(tasks)} concurrent fetches...", flush=True)
            fetch_results = await asyncio.gather(*tasks)
            print(f"DEBUG: [retrieval_node] Concurrent fetches completed.", flush=True)

        tool_response_parts = []
        fetch_idx = 0
        for fc in function_calls:
            tool_name = fc.name
            tool_args = dict(fc.args)
            
            if tool_name == "fetch_store_fn":
                result = fetch_results[fetch_idx]
                fetch_idx += 1
                slug = tool_args.get("slug")
                print(f"DEBUG: [retrieval_node] fetch_store_fn slug={slug} result success={result.get('success')}, count={len(result.get('products', [])) if result.get('products') else 0}", flush=True)
                if result.get("success"):
                    raw_products_accumulated.extend(result.get("products", []))
                    stores_responded += 1
                else:
                    if slug not in failed_stores:
                        failed_stores.append(slug)
                stores_queried += 1
                
                # Lightweight summary for LLM context
                openai_result = {
                    "success": result.get("success"),
                    "slug": slug,
                    "count": len(result.get("products", [])) if result.get("products") else 0
                }
            else:
                print(f"DEBUG: [retrieval_node] Executing other tool: {tool_name}", flush=True)
                try:
                    tool_func = TOOL_DISPATCH.get(tool_name)
                    if tool_func:
                        if tool_name == "filter_products_fn":
                            result = tool_func(raw_products_json=raw_products_accumulated, parsed_query_json=parsed_query)
                            filtered_products = result.get("products", [])
                            openai_result = {
                                "success": True,
                                "message": f"Successfully filtered products list. Output size: {len(filtered_products)}"
                            }
                        elif tool_name == "map_product_sizes_fn":
                            result = tool_func(products_json=filtered_products, measurements_json=measurements, generic_size=generic_size)
                            filtered_products = result.get("products", [])
                            openai_result = {
                                "success": True,
                                "message": f"Successfully mapped sizes. Output size: {len(filtered_products)}"
                            }
                        elif tool_name == "broaden_search_criteria_fn":
                            result = tool_func(parsed_query_json=parsed_query, strategy=tool_args.get("strategy", ""))
                            parsed_query = result
                            openai_result = result
                            print(f"DEBUG: [retrieval_node] broaden_search_criteria_fn relaxed query to: {parsed_query}", flush=True)
                            hint_parts = []
                            if parsed_query.get("color"):
                                hint_parts.append(parsed_query["color"])
                            if parsed_query.get("material"):
                                hint_parts.append(parsed_query["material"])
                            if parsed_query.get("item_type"):
                                hint_parts.append(parsed_query["item_type"])
                            search_hint = " ".join(hint_parts) if hint_parts else "kurta"
                        else:
                            result = tool_func(**tool_args)
                            openai_result = result
                    else:
                        openai_result = {"error": f"Tool '{tool_name}' not found"}
                except Exception as e:
                    openai_result = {"error": str(e)}

            resp_part = {
                "function_response": {
                    "name": tool_name,
                    "response": {"result": openai_result}
                }
            }
            tool_response_parts.append(resp_part)

        messages.append({"role": "user", "parts": tool_response_parts})

        # Break early if we have already accumulated at least 5 matching products
        if raw_products_accumulated:
            filter_res = filter_products_fn(raw_products_accumulated, parsed_query)
            filtered = filter_res.get("products", [])
            size_res = map_product_sizes_fn(filtered, measurements, generic_size)
            if len(size_res.get("products", [])) >= 5:
                break

    # --- Correctness Fallback ---
    if raw_products_accumulated:
        filter_res = filter_products_fn(raw_products_accumulated, parsed_query)
        filtered = filter_res.get("products", [])
        size_res = map_product_sizes_fn(filtered, measurements, generic_size)
        filtered_products = size_res.get("products", [])
    elif not filtered_products and state.get("filtered_products"):
        filtered_products = state.get("filtered_products")

    filtered_products.sort(key=lambda p: p.get("price", 0.0))
    filtered_products = filtered_products[:30]

    return {
        **state,
        "parsed_query": parsed_query,
        "search_hint": search_hint,
        "filtered_products": filtered_products,
        "failed_stores": failed_stores,
        "stores_queried": stores_queried,
        "stores_responded": stores_responded,
        "retrieval_iterations": current_iteration + 1
    }
