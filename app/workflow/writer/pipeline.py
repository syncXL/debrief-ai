from langgraph.graph import END, START, StateGraph
from . import nodes, state


def build_headliner():
    graph = StateGraph(state.base_state.WriteHeadline, output_schema=state.Output)
    graph.add_node("headliner", nodes.write_headline)
    
    graph.add_edge(START, "headliner")
    graph.add_edge("headliner", END)
    return  graph.compile()

def write_show_intro():
    graph = StateGraph(state.WriteShowIntro, output_schema=state.Output)
    graph.add_node("write_intro", nodes.write_show_intro)
    
    graph.add_edge(START, "write_intro")
    graph.add_edge("write_intro", END)
    return  graph.compile()

def conclude_show():
    graph = StateGraph(state.WriteShowConclusion, output_schema=state.Output)
    graph.add_node("conclude_show", nodes.conclude_show)
    
    graph.add_edge(START, "conclude_show")
    graph.add_edge("conclude_show", END)
    return  graph.compile()

def write_show_segment():
    graph = StateGraph(state.WriteStorySegment, output_schema=state.Output)
    graph.add_node("plan_show", nodes.plan_story)
    graph.add_node("write_show", nodes.write_plan)
    
    graph.add_edge(START, "plan_show")
    graph.add_edge("plan_show", "write_show")
    graph.add_edge("write_show", END)
    return  graph.compile()

def write_s2s():
    graph = StateGraph(state.Write_s2s_Transition, output_schema=state.Output)
    graph.add_node("s2s", nodes.s2s_transition)
    
    graph.add_edge(START, "s2s")
    graph.add_edge("s2s", END)
    return  graph.compile()

def write_h2s():
    graph = StateGraph(state.Write_h2s_transition, output_schema=state.Output)
    graph.add_node("h2s", nodes.h2s_transition)
    
    graph.add_edge(START, "h2s")
    graph.add_edge("h2s", END)
    return  graph.compile()

def conclude_episode():
    graph = StateGraph(state.WriteEpisodeConclusion, output_schema=state.Output)
    graph.add_node("conclude", nodes.conclude_episode)
    
    graph.add_edge(START, "conclude")
    graph.add_edge("conclude", END)
    return  graph.compile()    