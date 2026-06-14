from langchain_core.messages import HumanMessage, SystemMessage
from . import state, tools
from app import dependencies


async def get_rss_feeds(librarian_state: state.LibrarianState) -> state.LibrarianState:
    countries = ", ".join(tools.get_valid_countries())
    sections = ", ".join(tools.get_valid_countries())
    continents = ", ".join(tools.get_valid_countries())
    librarian_prompt = dependencies.load_instruction("prompts/librarian_prompt.md",
            countries=countries,
            sections=sections,
            continents=continents)
    sys_msg = SystemMessage(content=librarian_prompt)
    llm = dependencies.get_heavy_llm()
    if len(librarian_state["messages"]) == 0:
        message = f"""USER REQUEST: {librarian_state["refined_prompt"]} \n RECENCY WINDOW: {librarian_state["hours"]} hours"""
        human_message = HumanMessage(content=message)
        messages = [sys_msg] + [human_message]
    else:
        messages = [sys_msg] + librarian_state["messages"]
    response = await llm.ainvoke(messages,tools=tools.get_tools())
    return {"messages" : [response]}

