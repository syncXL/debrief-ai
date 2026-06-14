from typing import TypedDict, List
from .. import base_state

class WriteShowIntro(TypedDict):
    show : base_state.Show
    pos : int
    previous_show : str
    stories : List[base_state.Story]
    guests : List[base_state.Guest]

class WriteShowConclusion(TypedDict):
    show : base_state.Show
    pos : int
    stories : List[base_state.Story]
    guests : List[base_state.Guest]


class WriteStorySegment(TypedDict):
    show : base_state.Show
    story : base_state.Story
    pos : int
    story_pos : List[str]
    plan : str
    guests : List[base_state.Guest]


class Write_s2s_Transition(TypedDict):
    prev_show : base_state.Show
    prev_show_stories : List[base_state.Story]
    next_show : base_state.Show
    next_show_stories : List[base_state.Story]
    pos : int
    guests : List[base_state.Guest]


class WriteEpisodeConclusion(TypedDict):
    shows : List[base_state.Show]
    transcripts : List[base_state.Transcript]
    pos : int
    guests : List[base_state.Guest]


class Write_h2s_transition(TypedDict):
    shows : List[base_state.Show]
    pos : int
    guests : List[base_state.Guest]


class Output(TypedDict):
    transcripts : List[base_state.Script]