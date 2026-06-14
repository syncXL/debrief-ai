from langgraph.types import Send
from . import base_state

def distribute_story_to_researcher(debrief_state : base_state.DebriefState):
    return [Send("researcher", story) for story in debrief_state["stories"] if story.get("content")]


def distribute_story_to_personas(debrief_state : base_state.DebriefState):
    return [Send("persona", story) for story in debrief_state["stories"]]

def distribute_personas(story_state: base_state.Story):
    payload = []
    for ind in range(len(story_state["personas"])):
        sstate : base_state.PersonaParser = {
            "persona_id" : ind,
            "story" : story_state
        }
        payload.append(Send("extract_persona", sstate))
    return payload


#show intro
# conclude_show
# show_segment
# s2s 
# h2s .
