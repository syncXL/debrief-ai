import asyncio
import logging
from .pipelines import pipelines
from langgraph.types import Send,Command
from app import dependencies
from . import base_state

logger = logging.getLogger("debrief.workflow")


async def get_sources(episode_state: base_state.DebriefState) -> base_state.DebriefState:
    logger.info("[get_sources] Fetching sources for prompt: %s", episode_state.get("refined_prompt", "")[:80])
    req = {
        "refined_prompt" : episode_state["refined_prompt"],
        "hours" : episode_state["hours"],
    }
    librarian = pipelines.get("librarian")
    sources = await librarian.ainvoke(req)
    logger.info("[get_sources] Done — %d sources returned", len(sources.get("sources", [])))
    return {"sources" : sources["sources"]}


async def get_articles(episode_state: base_state.DebriefState) -> base_state.DebriefState:
    logger.info("[get_articles] Fetching articles from %d sources", len(episode_state.get("sources", [])))
    req = {
        "sources" : episode_state["sources"],
        "preferences" : episode_state["preference"],
        "n_story" : episode_state.get("n_story", 10)
    }
    herald = pipelines.get("herald")
    response = await herald.ainvoke(req)
    logger.info("[get_articles] Done — %d stories extracted", len(response.get("stories", [])))
    return {"stories" : response["stories"]}


async def research_article(story_state : base_state.Story) -> base_state.DebriefState:
    logger.info("[research_article] Researching: %s", story_state.get("title", "?"))
    req = {
        "title" : story_state["title"],
        "content" : story_state["content"]
    }
    researcher = pipelines.get("researcher")
    response = await researcher.ainvoke(req)
    story_state["context"] = response["context"]
    logger.info("[research_article] Done: %s", story_state.get("title", "?"))
    return {"stories" : [story_state] , "kb_contents" : response["kb_contents"]}


async def generate_audio(state: base_state.DebriefState) -> base_state.DebriefState:
    pending = [t for t in state.get("transcripts", []) if not t["script"].get("url")]
    logger.info("[generate_audio] Processing %d transcript(s) without audio", len(pending))
    generator = pipelines.get("tts")

    async def _synthesize(script_obj: dict) -> dict:
        node = script_obj["script"].get("node", "?")
        pos = script_obj["script"].get("pos", "?")
        logger.info("[generate_audio] Generating audio — node=%s pos=%s", node, pos)
        response = await generator.ainvoke(script_obj)
        logger.info("[generate_audio] Audio ready — node=%s pos=%s url=%s", node, pos, str(response.get("audio_url", "?"))[:60])
        return {**script_obj, "script": {**script_obj["script"], "url": response["audio_url"]}}

    updated = await asyncio.gather(*[_synthesize(s) for s in pending])
    return {"transcripts": list(updated)}


async def get_show(story_state : base_state.Story) -> base_state.Story:
    logger.info("[get_show] Routing story to shows: %s", story_state.get("title", "?"))
    req = {
        "content" : story_state.get("content", ""),
        "context" : story_state.get("context", ""),
        "published" : story_state["published"]
    }
    router = pipelines.get("show_router")
    response = await router.ainvoke(req)
    personas = [
        persona if isinstance(persona, dict) else persona.model_dump()
        for persona in response["persona_reasons"]
    ]
    story_state["personas"] = personas
    story_state["selected_shows"] = [
        show["show_id"] if isinstance(show, dict) else show.show_id
        for show in response["shows"]
    ]
    logger.info("[get_show] Story '%s' → shows: %s", story_state.get("title", "?"), story_state["selected_shows"])
    return {"stories" : [story_state]}


async def collect_shows(debrief_state : base_state.DebriefState) -> base_state.DebriefState:
    logger.info("[collect_shows] Building show lineup from %d stories", len(debrief_state.get("stories", [])))
    shows = {}
    guests = []
    for ind, story in enumerate(debrief_state["stories"]):
        if not story.get("content") or not story.get("selected_shows"):
            continue
        for show in story["selected_shows"]:
            if show in shows:
                shows[show]["stories"].append(ind)
                shows[show]["n_story"] += 1
            else:
                show_config = dependencies.load_config(f"prompts/shows/{show}/config.yaml")
                pos = "First" if len(shows) == 0 else "Middle"
                gids = []
                personas = show_config["personas"]
                for persona in personas:
                    persona_config = dependencies.load_config(f"prompts/personas/{persona}/config.yaml")
                    if persona not in [g["persona_id"] for g in guests]:
                        gid = len(guests)
                        guests.append({"persona_id" : persona, "config" : persona_config, "gid" : gid})
                        gids.append(gid)
                    else:
                        for guest in guests:
                            if guest["persona_id"] == persona:
                                gid = guest["gid"]
                        gids.append(gid)
                new_show : base_state.Show = {
                    "show_id" : show,
                    "tagline" : show_config["tagline"],
                    "n_story" : 1,
                    "stories" : [ind],
                    "pos" :  [pos],
                    "guests" : gids
                }
                shows[show] = new_show
    all_shows = list(shows.values())
    all_shows[-1]["pos"].append("Last show")
    logger.info("[collect_shows] Done — %d show(s), %d guest(s): %s",
                len(all_shows), len(guests), [s["show_id"] for s in all_shows])
    return {"shows" : all_shows, "guests" : guests}


async def get_persona_insights(persona_state : base_state.PersonaParser) -> base_state.Story:
    story = persona_state["story"]
    persona_dict = story["personas"].pop(persona_state["persona_id"])
    persona = pipelines.get("personas")
    content = "Main Story\n" + story.get("content", "") + "\nBackground \n" + story.get("context", "")
    response = await persona.ainvoke(
        {
            "persona_id" : persona_dict["persona_id"],
            "reason" : persona_dict["reason"],
            "article" :content
        }
    )
    persona = {
        "persona_id" :persona_dict["persona_id"],
        "reason" : persona_dict["reason"],
        "insight" : response["insight"]
    }
    story["personas"].append(persona)
    return story


async def process_all_personas(debrief_state: base_state.DebriefState) -> base_state.DebriefState:
    stories = [s for s in debrief_state.get("stories", []) if s.get("content") and s.get("personas")]
    logger.info("[process_all_personas] Getting persona insights for %d story/stories", len(stories))
    persona_pipeline = pipelines.get("persona")
    updated_stories = []
    for story in stories:
        processed = []
        content = "Main Story\n" + story["content"] + "\nBackground \n" + story.get("context", "")
        for p in story["personas"]:
            logger.info("[process_all_personas] persona=%s story=%s", p["persona_id"], story.get("title", "?")[:50])
            response = await persona_pipeline.ainvoke({
                "persona_id": p["persona_id"],
                "reason": p.get("reason", ""),
                "article": content,
            })
            processed.append({
                "persona_id": p["persona_id"],
                "reason": p.get("reason", ""),
                "insight": response["insight"],
            })
        updated_stories.append({**story, "personas": processed})
    logger.info("[process_all_personas] Done")
    return {"stories": updated_stories}


def distribute_after_research(debrief_state: base_state.DebriefState):
    valid_stories = [s for s in debrief_state["stories"] if s.get("content")]
    logger.info("[distribute_after_research] %d valid stories → dispatching headlines + show routing", len(valid_stories))
    headlines = []
    cur_pos = debrief_state.get("cur_pos", 0)
    headliner_config = dependencies.load_config("prompts/personas/headliner/config.yaml")
    guest : base_state.Guest = {
        "config" : headliner_config,
        "gid" : -1,
        "persona_id" : "headliner"
    }
    for ind in range(0, len(valid_stories), 5):
        tags = ["middle"] if ind != 0 else ["first"]
        stories = valid_stories[ind:ind+5]
        headlines.append({
            "stories": stories,
            "pos": cur_pos,
            "tags": tags,
            "guests" : [guest]
        })
        cur_pos += 1

    if len(headlines) == 1:
        headlines[-1]["tags"].append("last")
    else:
        headlines[-1]["tags"] = ["last"]

    shows = [Send("show_router", story) for story in valid_stories]
    payloads = [Send("headliner", headline) for headline in headlines] + shows
    logger.info("[distribute_after_research] Dispatching %d headline batch(es) + %d show router(s)", len(headlines), len(shows))
    return Command(update={"cur_pos": cur_pos}, goto=payloads)


async def get_historian_insight(debrief_state: base_state.DebriefState) -> base_state.DebriefState:
    stories = [s for s in debrief_state.get("stories", []) if s.get("content")]
    logger.info("[get_historian_insight] Adding historian to %d story/stories", len(stories))
    persona_pipeline = pipelines.get("persona")
    updated_stories = []
    for story in stories:
        persona_insights = "\n".join(
            f"### Persona:\n {p['persona_id']} \n ### Insights:\n {p.get('insight', '')}"
            for p in story.get("personas", [])
        )
        full_research = f"### Article :\n {story['content']} \n ### Context: \n {story.get('context', '')} \n  ### Insight: \n {persona_insights}"
        response = await persona_pipeline.ainvoke({
            "persona_id": "historian",
            "reason": "",
            "article": full_research,
        })
        historian = {"persona_id": "historian", "reason": "", "insight": response["insight"]}
        updated_stories.append({**story, "personas": [*story.get("personas", []), historian]})
        logger.info("[get_historian_insight] Done: %s", story.get("title", "?")[:60])
    return {"stories": updated_stories}


async def distribute_for_show_stage(debrief_state: base_state.DebriefState):
    shows = debrief_state["shows"]
    logger.info("[distribute_for_show_stage] Building write payloads for %d show(s): %s",
                len(shows), [s["show_id"] for s in shows])
    cur_pos = debrief_state["cur_pos"]
    headliner_config = dependencies.load_config("prompts/personas/headliner/config.yaml")
    headliner_guest : base_state.Guest = {
        "persona_id": "headliner",
        "gid": -1,
        "config": headliner_config,
    }
    payloads = [Send("h2s", {"shows": shows, "pos": cur_pos, "guests": [headliner_guest]})]
    cur_pos += 1
    prev_show = None
    prev_stories = []

    for show in shows:
        cur_stories = [debrief_state["stories"][ind] for ind in show["stories"]]
        cur_guests = [debrief_state["guests"][gid] for gid in show["guests"]]
        logger.info("[distribute_for_show_stage] show=%s stories=%d guests=%s",
                    show["show_id"], len(cur_stories), [g["persona_id"] for g in cur_guests])

        ## s2s
        if prev_show:
            s2s_transition = {
                "prev_show" : prev_show,
                "prev_show_stories" : prev_stories,
                "next_show" : show,
                "next_show_stories" : cur_stories,
                "pos" : cur_pos,
                "guests" : cur_guests,
            }
            cur_pos += 1
            payloads.append(Send("s2s", s2s_transition))

        ## intro
        show_req = {
            "show" : show,
            "pos" : cur_pos,
            "previous_show" : prev_show["show_id"] if prev_show else "",
            "stories" : cur_stories,
            "guests" : cur_guests,
        }
        payloads.append(Send("show_intro", show_req))
        cur_pos += 1

        ## per story segment
        for ind, story in enumerate(cur_stories):
            pos = ["First"] if ind == 0 else ["Middle"]
            if len(cur_stories) - 1 == ind:
                pos.append("Last")
            segment = {
                "show" : show,
                "story" : story,
                "pos" : cur_pos,
                "story_pos" : pos,
                "guests" : cur_guests,
            }
            payloads.append(Send("show_segment", segment))
            cur_pos += 1

        ## show conclusion
        conclusion = {
            "show" : show,
            "pos" : cur_pos,
            "stories" : cur_stories,
            "guests" : cur_guests,
        }
        show["conclude_id"] = cur_pos
        cur_pos += 1
        payloads.append(Send("conclude_show", conclusion))

        prev_show = show
        prev_stories = cur_stories

    # cur_pos is reserved for the episode conclusion (run after all shows complete)
    logger.info("[distribute_for_show_stage] Dispatching %d write tasks, ep_conclude pos=%d", len(payloads), cur_pos)
    return Command(update={"cur_pos": cur_pos, "shows": debrief_state["shows"]}, goto=payloads)


async def run_episode_conclusion(debrief_state: base_state.DebriefState) -> base_state.DebriefState:
    shows = debrief_state.get("shows", [])
    transcripts = debrief_state.get("transcripts", [])

    # Skip if episode conclusion was already written
    if any(
        isinstance(t, dict) and t.get("script", {}).get("node") == "conclude_episode"
        for t in transcripts
    ):
        return {}

    # Map pos → inner script dict for all transcripts currently in state
    transcripts_by_pos = {
        t["script"]["pos"]: t["script"]
        for t in transcripts
        if isinstance(t, dict) and "script" in t
    }

    # Only proceed once every show has its conclude_show transcript in state
    missing = [s["show_id"] for s in shows if s.get("conclude_id") not in transcripts_by_pos]
    if not shows or missing:
        logger.info("[run_episode_conclusion] Not ready yet — waiting on conclude_show for: %s", missing)
        return {}

    logger.info("[run_episode_conclusion] All show conclusions ready — writing episode conclusion")
    conclude_transcripts = [transcripts_by_pos[show["conclude_id"]] for show in shows]
    pos = debrief_state.get("cur_pos", 0)

    headliner_config = dependencies.load_config("prompts/personas/headliner/config.yaml")
    headliner_guest : base_state.Guest = {
        "persona_id": "headliner",
        "gid": -1,
        "config": headliner_config,
    }

    writer_pipeline = pipelines.get("conclude_episode")
    result = await writer_pipeline.ainvoke({
        "shows": shows,
        "transcripts": conclude_transcripts,
        "pos": pos,
        "guests": [headliner_guest],
    })

    # Generate audio for the episode conclusion inline (avoids the generate_audio loop)
    tts = pipelines.get("tts")
    updated = []
    for script_obj in result.get("transcripts", []):
        logger.info("[run_episode_conclusion] Generating audio for episode conclusion pos=%s", pos)
        audio_result = await tts.ainvoke(script_obj)
        updated.append({**script_obj, "script": {**script_obj["script"], "url": audio_result["audio_url"]}})

    logger.info("[run_episode_conclusion] Episode conclusion complete — pos=%s", pos)
    return {"transcripts": updated}
