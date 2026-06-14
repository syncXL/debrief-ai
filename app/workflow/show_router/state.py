from typing import TypedDict
from pydantic import BaseModel, Field
from .. import base_state

class RouterState(TypedDict):
    content :str
    context : str
    published : str

class PersonaReason(BaseModel):
    persona_id: base_state.PersonaID = Field(
        description=(
            "The exact persona ID. One entry per unique persona across all "
            "selected shows. Shared personas appear once with a unified reason."
        )
    )
    reason: str = Field(
        description=(
            "Two to three sentences stating what this persona will specifically "
            "surface in this story. Must name the specific actors, regulatory "
            "bodies, events, or mechanisms from the article or background context. "
            "For shared personas appearing in multiple selected shows, this reason "
            "must cover the persona's full contribution across all shows it serves — "
            "do not write separate reasons for each show. A generic domain match "
            "is not sufficient."
        )
    )

class Show(BaseModel):
    show_id: base_state.ShowID = Field(
        description="The exact show ID as defined in the show roster."
    )



class RouterOutput(BaseModel):
    shows: list[Show] = Field(
        description=(
            "List of selected shows. Minimum 1, maximum 3. "
            "The Brief counts toward the maximum only when it is the sole "
            "selection. Do not select The Brief alongside a named show. "
            "Historian and Anchor are assigned automatically — do not "
            "include them in show selection reasoning."
        )
    )
    persona_reasons: list[PersonaReason] = Field(
        description=(
            "One entry per unique persona needed across all selected shows. "
            "If two selected shows share a persona, that persona appears once "
            "with a unified reason — not twice. "
            "Historian and Anchor are excluded."
        )
    )

class RouterOutputTD(BaseModel):
    shows: list[dict] = Field(
        description=(
            "List of selected shows. Minimum 1, maximum 3. "
            "The Brief counts toward the maximum only when it is the sole "
            "selection. Do not select The Brief alongside a named show. "
            "Historian and Anchor are assigned automatically — do not "
            "include them in show selection reasoning."
        )
    )
    persona_reasons: list[dict] = Field(
        description=(
            "One entry per unique persona needed across all selected shows. "
            "If two selected shows share a persona, that persona appears once "
            "with a unified reason — not twice. "
            "Historian and Anchor are excluded."
        )
    )