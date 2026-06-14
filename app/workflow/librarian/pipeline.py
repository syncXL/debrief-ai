from langgraph.graph import  START, StateGraph
from . import state, nodes, tools
from langgraph.prebuilt import ToolNode, tools_condition


def get_pipeline():
    graph = StateGraph(state.LibrarianState, output_schema=state.Sources)
    graph.add_node("librarian", nodes.get_rss_feeds)
    graph.add_node("tools", ToolNode(tools=tools.get_tools()))

    graph.add_edge(START,"librarian")
    graph.add_conditional_edges("librarian", tools_condition)
    graph.add_edge("tools","librarian")

    return graph.compile()
