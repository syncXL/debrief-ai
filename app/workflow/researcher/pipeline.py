from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from . import state, nodes, tools

def get_pipeline():
    graph = StateGraph(state.ResearcherState, output_schema=state.OutputState)
    graph.add_node("researcher", nodes.research_article)
    graph.add_node("add_context", nodes.add_context)
    graph.add_node("tools", ToolNode(tools.get_tools()))

    graph.add_edge(START, "researcher")
    graph.add_conditional_edges("researcher", tools_condition,{"tools": "tools", "__end__": "add_context"})
    graph.add_edge("tools", "researcher")
    graph.add_edge("add_context", END)

    return graph.compile()