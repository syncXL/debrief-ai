from langgraph.graph import START, END, StateGraph
from . import state, nodes


def get_pipeline():
    graph = StateGraph(state.InquisitorState, output_schema=state.SearchOutput)
    graph.add_node("search", nodes.search)
    graph.add_edge(START, "search")
    graph.add_edge("search", END)
    return graph.compile()