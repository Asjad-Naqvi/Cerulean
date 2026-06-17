from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.planner_agent import planner_node
from agents.retrieval_agent import retrieval_node, SPARSE_THRESHOLD, MAX_ITERATIONS
from agents.ranker_agent import ranker_node

def route_after_retrieval(state: AgentState) -> str:
    """
    Conditional routing edge checking if we need to broaden query and repeat retrieval.
    """
    filtered = state.get("filtered_products") or []
    iterations = state.get("retrieval_iterations", 0)
    
    if len(filtered) < SPARSE_THRESHOLD and iterations < MAX_ITERATIONS:
        return "retrieval"
    return "ranker"

# Initialize graph with state schema
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planner", planner_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("ranker", ranker_node)

# Set entry point
workflow.set_entry_point("planner")

# Standard edge
workflow.add_edge("planner", "retrieval")

# Conditional loop edge
workflow.add_conditional_edges(
    "retrieval",
    route_after_retrieval,
    {
        "retrieval": "retrieval",
        "ranker": "ranker"
    }
)

# End edge
workflow.add_edge("ranker", END)

# Compile graph
fashion_graph = workflow.compile()
