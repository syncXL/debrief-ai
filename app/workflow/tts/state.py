from typing import TypedDict, List
from .. import base_state



class Output(TypedDict):
    transcript : str
    audio_url : str
    