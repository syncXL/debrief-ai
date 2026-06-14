from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from app import dependencies
from . import state, tools

async def search(inquisitor_state : state.InquisitorState) -> state.SearchOutput:

    llm = dependencies.get_heavy_llm()
    query = inquisitor_state["query"]
    kb_client = dependencies.get_kb_client()
    cypher_docs = dependencies.load_instruction("prompts/archivist/cypher_read.md")
    labels = await kb_client.get_labels()
    instruction = dependencies.load_instruction("prompts/inquisitor.md", labels=", ".join(labels), doc=cypher_docs)
    search_agent = create_agent(llm.client,tools=tools.get_tools(), system_prompt=instruction)
    response = await search_agent.ainvoke({"messages": [HumanMessage(content=query)]})
    final_msg = response["messages"][-1]
    content = final_msg.content if isinstance(final_msg.content, str) else ""

    output = await llm.ainvoke([HumanMessage(content=f"Convert this response into the required schema:\n\n{content}")],schema=state.SearchOutput)
    return output.model_dump()