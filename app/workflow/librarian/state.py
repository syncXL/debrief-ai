from typing import TypedDict, List, Annotated
from langgraph.graph import MessagesState
from operator import add
from .. import base_state

class LibrarianState(MessagesState):
    refined_prompt : str
    hours : str
    sources: Annotated[List[base_state.Source], add]

class Sources(TypedDict):
    sources: List[base_state.Source]