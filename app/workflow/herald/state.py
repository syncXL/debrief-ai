from typing import TypedDict,List
from pydantic import BaseModel, Field
from .. import base_state

class Story(BaseModel):
    title: str = Field(
        description=(
            "A clean, neutral headline that represents the story across all its source articles. "
            "Should be specific enough to distinguish this story from others, and written as a "
            "professional news headline — not a sentence, not a question. "
            "Example: 'CBN Holds Interest Rate at 27.5% for Second Consecutive Meeting'"
        )
    )

    published : str = Field(description="The published date, choose the earliest date in formmat YYYY/MM/DD")
    reason : str = Field(description="explain in 1-2 sentences WHY these articles belong together (or why this article stands alone)")
    articles_id: List[str] = Field(
        description=(
            "The list of article IDs that cover this story. Each ID must be returned exactly "
            "as provided in the input, in the format DD_DD (e.g. '03_07', '11_42'). "
            "Do not modify, reformat, or truncate any ID. "
            "Every article ID must appear in exactly one story — no duplicates, no omissions."
        )
    )
    section: List[str] = Field(
        description=(
            "The list of section labels that apply to this story. "
            "Must only contain values from this fixed vocabulary: "
            "Finance, Business, Markets, Politics, Policy, Government, "
            "World, International, Geopolitics, Technology, AI, Startups, "
            "Sport, Entertainment, Culture, Health, Climate, Energy. "
            "Use as many labels as genuinely apply. Do not invent new labels."
        )
    )


class Stories(BaseModel):
    stories: List[Story] = Field(
        description=(
            "The complete list of grouped stories derived from the input articles. "
            "Every article from the input must appear in exactly one story. "
            "A story may contain only one article — single-source stories are valid."
        )
    )

def merge_stories(existing: list, new: list) -> list:
    def to_story(p):
        return Story(**p) if isinstance(p, dict) else p

    existing_map = {p.title: p for p in map(to_story, existing)}
    for p in map(to_story, new):
        existing_map[p.title] = p
    return list(existing_map.values())

class StoryWithContent(Story):
    story : Story
    related_articles : List[base_state.Article]

class HeraldState(TypedDict):
    sources: List[base_state.Source]
    stories: base_state.Annotated[List[base_state.Story], base_state.merge_stories]
    preferences : str
    n_story : int


class OutputState(TypedDict):
    stories: List[base_state.Story]