from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # Inputs
    raw_query: Optional[str]
    image_bytes: Optional[bytes]
    image_mime_type: Optional[str]
    measurements: Optional[Dict[str, float]] # e.g. {"chest": 35.5, "waist": 29.0, "hips": 39.0}
    gender_constraint: Optional[str] # e.g. "men", "women", "kids", "any"
    
    # Planner outputs
    parsed_query: Optional[Dict[str, Any]]
    target_store_slugs: Optional[List[str]]
    search_hint: Optional[str]
    
    # Retrieval outputs
    filtered_products: Optional[List[Dict[str, Any]]]
    failed_stores: Optional[List[str]]
    stores_queried: Optional[int]
    stores_responded: Optional[int]
    retrieval_iterations: int
    
    # Ranker outputs
    ranked_products: Optional[List[Dict[str, Any]]]
    search_summary: Optional[str]
