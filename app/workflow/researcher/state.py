from typing import TypedDict, List
from langgraph.graph import MessagesState
from .. import base_state

class ResearcherState(MessagesState):
    title : str
    content : str

class OutputState(TypedDict):
    context : str
    kb_contents : List[base_state.AddToKB]
