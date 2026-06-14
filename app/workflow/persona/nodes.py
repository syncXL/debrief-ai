from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from app import dependencies
from . import state

async def process_persona(persona_state : state.PersonaState) -> state.PersonaOutput:
    llm = dependencies.get_heavy_llm()
    sys_instr = dependencies.load_instruction(
        f"prompts/personas/{persona_state["persona_id"]}/doc.md",
        reason=persona_state["reason"]
    )
    hum_msg = HumanMessage(content=persona_state["article"])
    persona_ag = create_agent(model=llm.client, tools=[{"type": "web_search"}], system_prompt=sys_instr)
    response = await persona_ag.ainvoke({"messages" : [hum_msg]})
    insight = response["messages"][-1].text
    return {"insight" : insight}