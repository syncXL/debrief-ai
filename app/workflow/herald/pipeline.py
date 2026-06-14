from langgraph.graph import END, START, StateGraph
from . import nodes, state, edges

def get_pipeline():
    graph = StateGraph(state.HeraldState, output_schema=state.OutputState)
    graph.add_node("grouper", nodes.group_articles)
    graph.add_node("extractor", nodes.extract_story)

    graph.add_edge(START, "grouper")
    graph.add_conditional_edges("grouper", edges.distribute_story,{"extractor" : "extractor", "__end__" : "__end__"})
    graph.add_edge("extractor", END)
    return graph.compile()