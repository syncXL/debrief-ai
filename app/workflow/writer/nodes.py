import logging
from . import state
from .. import base_tools, base_state
from app import dependencies
from . import tools
from langchain.messages import HumanMessage

logger = logging.getLogger("debrief.writer")

async def write_headline(headline_state : state.base_state.WriteHeadline) -> state.Output:
    logger.info("[write_headline] pos=%s tags=%s stories=%d", headline_state.get("pos"), headline_state.get("tags"), len(headline_state.get("stories", [])))
    current_date = base_tools.current_datetime_string()
    llm = dependencies.get_max_llm()
    message = dependencies.load_instruction(
        "prompts/writer/headline_transcript.md",
        current_date=current_date,
        batch_position=", ".join(headline_state.get("tags", [])),
        stories= "\n".join([base_tools.format_story(story) for story in headline_state["stories"] ])
    )
    response = await llm.ainvoke([HumanMessage(content=message)])
    transcript: base_state.Transcript = {
        "pos" : headline_state["pos"],
        "sketch" : response.text,
        "tag" : headline_state.get("tags", []),
        "type" : 0,
        "node" : "headlines"
    }
    return {
        "transcripts" : [{"script" : transcript, "guests" : headline_state["guests"]}],
    }

async def write_show_intro(show_state : state.WriteShowIntro) -> state.Output:
    logger.info("[write_show_intro] show=%s pos=%s", show_state["show"]["show_id"], show_state.get("pos"))
    current_date = base_tools.current_datetime_string()
    llm = dependencies.get_max_llm()
    guests = "\n".join([tools.base_tools.format_persona_config(guest["config"]) for guest in show_state["guests"]])
    stories = "\n".join(
        f"Title:\n{s['title']}\nContent:\n{s['content']}"
        for s in show_state["stories"]
    )

    message = dependencies.load_instruction(
        "prompts/writer/show_intro.md",
        current_date=current_date,
        show_name=show_state["show"]["show_id"],
        show_tagline=show_state["show"]["tagline"],
        episode_position=", ".join(show_state["show"]["pos"]),
        previous_show_name=show_state["previous_show"],
        previous_personas="",
        personas=guests,
        stories=stories
    )

    response = await llm.ainvoke([HumanMessage(content=message)])
    transcript : base_state.Transcript = {
        "pos" : show_state["pos"],
        "sketch" : response.text,
        "tag" : show_state["show"].get("tag", ""),
        "type" : 1,
        "node" : "show_intro"
    }
    return {
        "transcripts" : [{"script" : transcript, "guests" : show_state["guests"]}],
    }

async def conclude_show(show_state : state.WriteShowConclusion) -> state.Output:
    logger.info("[conclude_show] show=%s pos=%s", show_state["show"]["show_id"], show_state.get("pos"))
    llm = dependencies.get_max_llm()
    current_date = base_tools.current_datetime_string()
    show_name = show_state["show"]["show_id"]
    tagline = show_state["show"]["tagline"]
    titles = "\n".join([story["title"] for story in show_state["stories"]])

    message = dependencies.load_instruction(
        "prompts/writer/show_conclusion.md",
        current_date=current_date,
        show_name=show_name,
        show_tagline=tagline,
        story_titles=titles
    )

    response = await llm.ainvoke([HumanMessage(content=message)])
    transcript: base_state.Transcript = {
        "pos" : show_state["pos"],
        "sketch" : response.text,
        "tag" : show_state["show"].get("tag", ""),
        "type" : 0,
        "node" : "conclude_show"
    }

    return {
        "transcripts" : [{"script" : transcript, "guests" : show_state["guests"]}],
    }

async def plan_story(show_state : state.WriteStorySegment) -> state.WriteStorySegment:
    logger.info("[plan_story] show=%s story=%s pos=%s", show_state["show"]["show_id"], show_state["story"].get("title", "?")[:50], show_state.get("pos"))
    llm = dependencies.get_max_llm()
    current_date = base_tools.current_datetime_string()
    story = show_state["story"]
    personas_str, historian = tools._build_personas_str(story, show_state["guests"])


    message = dependencies.load_instruction(
        "prompts/writer/planner.md",
        current_date=current_date,
        show_name = show_state["show"]["show_id"],
        story_position= ", ".join(show_state["story_pos"]),
        personas=personas_str,
        article=story.get("content", ""),
        published_date=story["published"],
        background_context=story.get("context", ""),
        historian_context=historian
    )

    response = await llm.ainvoke([HumanMessage(content=message)])
    return {"plan" : response.text}

async def write_plan(show_state : state.WriteStorySegment) -> state.Output:
    logger.info("[write_plan] show=%s story=%s pos=%s", show_state["show"]["show_id"], show_state["story"].get("title", "?")[:50], show_state.get("pos"))
    llm = dependencies.get_max_llm()
    current_date = base_tools.current_datetime_string()
    story = show_state["story"]
    personas_str, historian = tools._build_personas_str(story, show_state["guests"])
    message = dependencies.load_instruction(
        "prompts/writer/writer.md",
        current_date=current_date,
        published_date=story["published"],
        plan=show_state["plan"],
        personas=personas_str,
        article=story.get("content", ""),
        background_context=story.get("context", ""),
        historian_context=historian
    )

    response = await llm.ainvoke([HumanMessage(content=message)])
    transcript: base_state.Transcript = {
        "pos" : show_state["pos"],
        "sketch" : response.text,
        "tag" : show_state["show"].get("tag", ""),
        "type" : 0,
        "node" : "show_segment"
    }

    return {
        "transcripts" : [{"script" : transcript, "guests" : show_state["guests"]}],
    }

async def s2s_transition(show_state : state.Write_s2s_Transition) -> state.Output:
    logger.info("[s2s_transition] %s → %s pos=%s", show_state["prev_show"]["show_id"], show_state["next_show"]["show_id"], show_state.get("pos"))
    llm = dependencies.get_max_llm()
    current_date = base_tools.current_datetime_string()
    prev_show_name = show_state["prev_show"]["show_id"]
    prev_show_tagline = show_state["prev_show"]["tagline"]
    prev_show_titles = ", ".join([story["title"] for story in show_state["prev_show_stories"]])

    next_show_name = show_state["next_show"]["show_id"]
    next_show_tagline = show_state["next_show"]["tagline"]
    next_show_titles = ", ".join([story["title"] for story in show_state["next_show_stories"]])

    message = dependencies.load_instruction(
        "prompts/writer/show_to_show_transition.md",
        current_date=current_date,
        prev_show_name=prev_show_name,
        prev_show_tagline=prev_show_tagline,
        prev_show_story_titles=prev_show_titles,
        next_show_name=next_show_name,
        next_show_tagline=next_show_tagline,
        next_show_story_titles=next_show_titles
    )
    response = await llm.ainvoke([HumanMessage(content=message)])

    transcript: base_state.Transcript = {
        "pos" : show_state["pos"],
        "sketch" : response.text,
        "tag" : "",
        "type" : 0,
        "node" : "show_to_show"
    }

    return {
        "transcripts" : [{"script" : transcript, "guests" : show_state["guests"]}],
    }

async def h2s_transition(show_state : state.Write_h2s_transition) ->state.Output:
    logger.info("[h2s_transition] pos=%s shows=%s", show_state.get("pos"), [s["show_id"] for s in show_state.get("shows", [])])
    llm = dependencies.get_max_llm()

    current_date = base_tools.current_datetime_string()
    shows = []
    for show in show_state["shows"]:
        fmt = f"Name: {show["show_id"]} \n Tagline: {show["tagline"]} \n N_Stories: {show["n_story"]}"
        shows.append(fmt)
    shows = "\n".join(shows)

    message = dependencies.load_instruction(
        "prompts/writer/headline_to_show_transition.md",
        current_date=current_date,
        shows=shows
    )

    response = await llm.ainvoke([HumanMessage(content=message)])
    transcript: base_state.Transcript = {
        "pos" : show_state["pos"],
        "sketch" : response.text,
        "tag" : "",
        "type" : 0,
        "node" : "headline_to_show"
    }
    return {
        "transcripts" : [{"script" : transcript, "guests" : show_state["guests"]}],
    }

async def conclude_episode(show_state : state.WriteEpisodeConclusion) -> state.Output:
    logger.info("[conclude_episode] pos=%s shows=%d transcripts=%d", show_state.get("pos"), len(show_state.get("shows", [])), len(show_state.get("transcripts", [])))
    llm = dependencies.get_max_llm()
    current_date = base_tools.current_datetime_string()
    show_conclusions = []
    for ind, show in enumerate(show_state["shows"]):
        transcript = show_state["transcripts"][ind] if ind < len(show_state["transcripts"]) else {}
        sketch = transcript.get("sketch", "") if isinstance(transcript, dict) else ""
        show_conclusions.append(f"Show: {show['show_id']}\nTagline: {show.get('tagline', '')}\n{sketch}")
    show_conclusions = "\n\n".join(show_conclusions)

    message = dependencies.load_instruction(
        "prompts/writer/episode_conclusion.md",
        current_date=current_date,
        show_conclusions=show_conclusions
    )

    response = await llm.ainvoke([HumanMessage(content=message)])

    transcript: base_state.Transcript = {
        "pos" : show_state["pos"],
        "sketch" : response.text,
        "tag" : "",
        "type" : 0,
        "node" : "conclude_episode"
    }
    return {
    "transcripts" : [{"script" : transcript, "guests" : show_state["guests"]}],
    }