
from . import state
from typing import Union


def route_after_tools(kb_state : Union[state.Archiver, state.ExtractRels, state.ExtractNodes]):
    return kb_state["tool_caller"]
