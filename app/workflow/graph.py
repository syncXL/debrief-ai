from . import pipelines
from langgraph.graph import StateGraph, START, END
from . import base_state
from . import nodes, edges
##interpreter
# librarian
#  herald
# researcher
# writer: headliner#
# show_router 
# persona 
# writer:
    # h2s
    # s2s
    # show
    # sconc
    # epiconc#
# archivist#

def build_graph():
    graph = StateGraph(base_state.DebriefState)
    graph.add_node("interpreter", pipelines.pipelines.get("interpreter"))
    graph.add_node("librarian", nodes.get_sources)
    graph.add_node("herald", nodes.get_articles)
    graph.add_node("extract_historian", nodes.get_historian_insight)
    graph.add_node("researcher", nodes.research_article)
    graph.add_node("distr_after_research", nodes.distribute_after_research)
    graph.add_node("collect_shows", nodes.collect_shows)
    graph.add_node("LCA", nodes.distribute_for_show_stage)
    graph.add_node("headliner", pipelines.pipelines.get("headliner"))
    graph.add_node("show_intro", pipelines.pipelines.get("show_intro"))
    graph.add_node("conclude_show", pipelines.pipelines.get("conclude_show"))
    graph.add_node("show_segment", pipelines.pipelines.get("show_segment"))
    graph.add_node("s2s", pipelines.pipelines.get("s2s"))
    graph.add_node("h2s", pipelines.pipelines.get("h2s"))
    graph.add_node("run_episode_conclusion", nodes.run_episode_conclusion)
    graph.add_node("generate_audio", nodes.generate_audio)
    graph.add_node("show_router", nodes.get_show)
    graph.add_node("personas", nodes.process_all_personas)

    graph.add_edge(START, "interpreter")
    graph.add_edge("interpreter", "librarian")
    graph.add_edge("librarian", "herald")
    graph.add_conditional_edges("herald",edges.distribute_story_to_researcher)
    graph.add_edge("researcher", "distr_after_research")
    graph.add_edge("show_router", "collect_shows")
    graph.add_edge("collect_shows", "personas")
    graph.add_edge("personas", "extract_historian")
    graph.add_edge("extract_historian", "LCA")
    graph.add_edge("headliner", "generate_audio")
    graph.add_edge("show_intro", "generate_audio")
    graph.add_edge("conclude_show", "generate_audio")
    graph.add_edge("show_segment", "generate_audio")
    graph.add_edge("s2s", "generate_audio")
    graph.add_edge("h2s", "generate_audio")
    graph.add_edge("generate_audio", "run_episode_conclusion")
    graph.add_edge("run_episode_conclusion", END)
    return graph.compile()



### edges
### update state operators
