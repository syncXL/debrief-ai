from langgraph.graph import END, START, StateGraph
from . import state, nodes


def get_pipeline():
    graph = StateGraph(state.PersonaState, output_schema=state.PersonaOutput)
    graph.add_node("process_persona", nodes.process_persona)
    graph.add_edge(START, "process_persona")
    graph.add_edge("process_persona", END)
    return graph.compile()