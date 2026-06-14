from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from . import state, tools
from app import dependencies

async def identify_nodes(kb_state : state.ExtractNodes) -> state.ExtractNodes:
    background_context = kb_state["context"]
    llm = dependencies.get_heavy_llm()
    doc = dependencies.load_instruction("prompt/archivist/cypher_read.md")
    neo4j = dependencies.get_kb_client()
    label = neo4j.get_labels()
    instruction = dependencies.load_instruction("prompt/archivist/node_prompt.md",
                existing_labels=label,
                existing_relationship_types="",
                doc=doc)
    instruction = SystemMessage(instruction)
    hm_msg = HumanMessage(content=background_context)
    if len(kb_state["messages"]) == 0:
        messages = [hm_msg]
    else:
        messages = kb_state["messages"]
    agent = create_agent(model=llm.client, tools=tools.get_tools(),system_prompt=instruction)
    response = await agent.ainvoke({"messages" :messages})
    msgs = response.get("messages", response) if isinstance(response, dict) else response
    return {"messages"  : msgs, "tool_caller" : "node_extract"}

async def route_to_relationships(kb_state : state.ExtractNodes) -> state.ExtractRels:
    nodes = kb_state["messages"][-1].text
    return {"context" : kb_state["context"],  "nodes" : nodes}

async def identify_relationships(kb_state: state.ExtractRels) -> state.ExtractRels:
    background_context = kb_state["context"]
    neo4j = dependencies.get_kb_client()
    llm = dependencies.get_heavy_llm()
    label = neo4j.get_labels()
    doc = dependencies.load_instruction("prompt/archivist/cypher_read.md")
    nodes = kb_state["nodes"]
    nodes = "\n".join(nodes)
    instruction = dependencies.load_instruction("prompt/archivist/relationship_prompt.md", 
            doc=doc,
            resolved_nodes=nodes,
            existing_labels=label,
            existing_relationship_types="")
    instruction = SystemMessage(instruction)
    hm_msg = HumanMessage(content=background_context)
    if len(kb_state["messages"]) == 0:
        messages = [hm_msg]
    else:
        messages = kb_state["messages"]
    agent = create_agent(model=llm.client, tools=tools.get_tools(),system_prompt=instruction)
    response = agent.ainvoke({"messages" :messages})
    # Extract messages from response if it's a dict, otherwise use response directly
    msgs = response.get("messages", response) if isinstance(response, dict) else response
    return {"messages" : msgs, "tool_caller" : "rels"}


async def route_to_writer(kb_state : state.ExtractRels) -> state.Archiver:
    rels = kb_state["messages"][-1].text
    nodes = kb_state["nodes"]
    llm = dependencies.get_heavy_llm()
    
    instruction = dependencies.load_instruction("prompts/archivist/structure_output.md", node_pass_output=nodes, relationship_pass_output=rels)
    knowledge = llm.ainvoke([HumanMessage(instruction)],schema=state.Output)
    return {"nodes" : nodes, "full_knowledge" : knowledge, "relationships" : rels}


async def write_query(kb_state : state.Archiver)-> state.Archiver:
    doc = dependencies.load_instruction("prompt/archivist/cypher_write.md")
    knowledge = kb_state.get("full_knowledge", None)
    llm = dependencies.get_heavy_llm()


    instruction = dependencies.load_instruction("prompts/archivist/cypher.md", doc=doc)
    
    if len(kb_state["messages"]) == 0:
        nodes = "\n".join([node.model_dump_json(indent=2) for node in knowledge.nodes])
        rels = "\n".join([rel.model_dump_json(indent=2) for rel in knowledge.rels])
        hm_msg = HumanMessage(content=f"""Nodes: \n {nodes} \n Relationships: \n{rels}""")
        messages = [hm_msg]
    else:
        messages = kb_state["messages"]
    agent = create_agent(model=llm, tools=tools.get_tools(),system_prompt=instruction)
    response = agent.ainvoke({"messages" :messages})
    msgs = response.get("messages", response) if isinstance(response, dict) else response
    return {"messages" : msgs, "tool_caller" : "write"}