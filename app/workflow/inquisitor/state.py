from typing import TypedDict
from pydantic import BaseModel, Field


class InquisitorState(TypedDict):
    query : str

class SearchOutput(BaseModel):
    known_context: str = Field(
        default="",
        description="Facts sourced from the knowledge graph. The user has encountered these before."
    )
    new_context: str = Field(
        default="",
        description="Facts sourced from web search. Net-new to the user."
    )
    add_to_kb: bool = Field(default=False)
    cite: list[str] = Field(default_factory=list)
