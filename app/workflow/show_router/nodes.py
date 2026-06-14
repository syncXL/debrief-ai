from langchain_core.messages import HumanMessage
from . import state
from app import dependencies


async def select_shows(router_state: state.RouterState) -> state.RouterOutputTD:
    llm = dependencies.get_heavy_llm()
    msg = [HumanMessage(content=dependencies.load_instruction(
        "prompts/router.md",
        article=router_state["content"],
        context=router_state["context"],
        article_date=router_state["published"]
    ))]
    output : state.RouterOutput = await llm.ainvoke(msg, schema=state.RouterOutput)
    shows = [show.model_dump() for show in output.shows]
    personas = [persona.model_dump() for persona in output.persona_reasons]
    return {"shows" : shows, "persona_reasons" : personas}