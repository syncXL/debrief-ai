from typing import TypedDict


class PersonaState(TypedDict):
    persona_id : str
    reason : str
    article : str

class PersonaOutput(TypedDict):
    insight : str