from langgraph.graph import StateGraph, START, END
from . import nodes
from .. import base_state


def get_pipeline():
    graph = StateGraph(base_state.DebriefState)
    graph.add_node("refiner", nodes.refine_prompt)

    graph.add_edge(START, "refiner")
    graph.add_edge("refiner", END)
    return graph.compile()