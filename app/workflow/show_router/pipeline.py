from langgraph.graph import END, START, StateGraph
from . import nodes, state

def get_pipeline():

    graph = StateGraph(state.RouterState, output_schema=state.RouterOutput)
    graph.add_node("router", nodes.select_shows)
    graph.add_edge(START, "router")
    graph.add_edge("router",END)

    return graph.compile()