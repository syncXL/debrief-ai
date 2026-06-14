from typing import TypedDict, List, Literal
from typing_extensions import Annotated
from operator import add

ShowID = Literal[
    "economy_today",
    "political_pulse",
    "world_affairs",
    "tech_decoded",
    "socialite_report",
    "science_and_society",
    "headline"
]

PersonaID = Literal[
    "banker",
    "critic",
    "economist",
    "geopolitician",
    "historian",
    "lawyer",
    "politician",
    "scientist",
    "socialite",
    "tech_analyst"
]

def merge_personas(existing: list, new: list) -> list:
    # new personas override existing ones by name
    existing_map = {p["persona_id"]: p for p in existing}
    for p in new:
        existing_map[p["persona_id"]] = p
    return list(existing_map.values())

def merge_stories(existing: list, new: list) -> list:
    # new personas override existing ones by name
    existing_map = {p["title"]: p for p in existing}
    for p in new:
        existing_map[p["title"]] = p
    return list(existing_map.values())

def merge_shows(existing: list, new: list) -> list:
    # new personas override existing ones by name
    existing_map = {p["show_id"]: p for p in existing}
    for p in new:
        existing_map[p["show_id"]] = p
    return list(existing_map.values())

def merge_guests(existing: list, new: list) -> list:
    # new personas override existing ones by name
    existing_map = {p["gid"]: p for p in existing}
    for p in new:
        existing_map[p["gid"]] = p
    return list(existing_map.values())

def merge_transcripts(existing: list, new: list) -> list:
    # new personas override existing ones by name
    existing_map = {p["script"]["pos"]: p for p in existing}
    for p in new:
        existing_map[p["script"]["pos"]] = p
    return list(existing_map.values())



class AddToKB(TypedDict):
    query : str
    content : str


class Transcript(TypedDict):
    pos : int
    tag : str
    sketch : str
    script : str
    url : str
    type : Literal[0, 1]
    node : str


class Article(TypedDict):
    title: str
    summary : str
    link: str
    published : str


class Source(TypedDict):
    country : str
    section : str
    feed_name: str
    rss_link : str
    articles : list[Article]

class Persona(TypedDict):
    persona_id : str
    insight : str
    reason : str

class Story(TypedDict):
    title : str
    articles : List[str]
    content: str
    context : str
    links : List[str]
    published : str
    sections : List[str]
    reason : str
    personas : Annotated[List[Persona],merge_personas]
    selected_shows : List[ShowID]

class PersonaParser(TypedDict):
    story : Story
    persona_id : int


class Guest(TypedDict):
    gid : int
    persona_id : PersonaID
    config : dict

class WriteHeadline(TypedDict):
    stories : List[Story]
    pos : int
    tags : List[str]
    guests : List[Guest]


class Script(TypedDict):
    guests : List[Guest]
    script : Transcript
    


class Show(TypedDict):
    show_id: ShowID
    stories : List[int]
    tagline : str
    tag : str 
    # pos : int
    conclude_id : int
    n_story : int
    show_type : str
    guests : List[int]



class DebriefState(TypedDict):
    cur_pos : int
    preference : str
    refined_prompt : str
    hours : int
    n_story : int
    sources : Annotated[List[Source], add]
    stories : Annotated[List[Story], merge_stories]
    shows : Annotated[List[Show], merge_shows]
    guests : Annotated[List[Guest], merge_guests]
    transcripts : Annotated[List[Script], merge_transcripts] ## Conclusion
    kb_contents : Annotated[List[AddToKB], add]

