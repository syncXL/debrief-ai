from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode,tools_condition
from . import nodes, edges, state,tools

def get_pipeline():
    graph = StateGraph(state.ExtractNodes, output_schema=state.Archiver)
    graph.add_node("node_extract", nodes.identify_nodes)
    graph.add_node("route_to_rel", nodes.route_to_relationships)
    graph.add_node("route_to_write", nodes.route_to_writer)
    graph.add_node("rels", nodes.identify_relationships)
    graph.add_node("write", nodes.write_query)
    graph.add_node("tools", ToolNode(tools.get_tools()))


    graph.add_edge(START, "node_extract")
    graph.add_edge("route_to_rel", "rels")
    graph.add_edge("route_to_write", "write")
    # graph.add_conditional_edges("tools", route_after_tools, {
    #     "node_extract": "node_extract",
    #     "rels": "rels",
    #     "write": "write"
    # })
    graph.add_conditional_edges(
        "node_extract", 
        tools_condition, 
        {"__end__": "route_to_rel", "tools": "tools"}  # ← add this
    )

    graph.add_conditional_edges(
        "rels", 
        tools_condition, 
        {"__end__": "route_to_write", "tools": "tools"}  # ← add this
    )

    graph.add_conditional_edges(
        "write", 
        tools_condition,
        {"__end__": END, "tools": "tools"}  # ← add explicit mapping here too
    )

    # route_after_tools stays the same
    graph.add_conditional_edges("tools", edges.route_after_tools, {
        "node_extract": "node_extract",
        "rels": "rels",
        "write": "write"
    })

    return graph.compile()