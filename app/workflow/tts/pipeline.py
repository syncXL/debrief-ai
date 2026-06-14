from langgraph.graph import END, START, StateGraph
from . import state, nodes

def get_pipeline():
    graph = StateGraph(state.base_state.Script, output_schema=state.Output)
    graph.add_node("convert", nodes.convert_to_ssml)
    graph.add_node("synthesize", nodes.synthesize_transcript)

    graph.add_edge(START, "convert")
    graph.add_edge("convert", "synthesize")
    graph.add_edge("synthesize",END)
    return graph.compile()