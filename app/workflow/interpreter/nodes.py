from langchain_core.messages import HumanMessage, SystemMessage
from .. import base_state as root
from . import state
from app import dependencies

async def refine_prompt(debrief_state: root.DebriefState) -> root.DebriefState:
    instruction = SystemMessage(content=dependencies.load_instruction("prompts/interpreter.md"))
    messages= [instruction, HumanMessage(debrief_state["preference"])]
    llm = dependencies.get_heavy_llm()
    output = await llm.ainvoke(messages,schema=state.Preference)
    return {"hours" : output.hours , "refined_prompt" : output.refined_prompt}
