from langchain_core.messages import HumanMessage
from . import state, tools
from app import dependencies

async def group_articles(herald_state: state.HeraldState) -> state.HeraldState:
    llm = dependencies.get_heavy_llm()
    formatted_sources = []
    for ind, source in enumerate(herald_state["sources"]):
        src_id = f"{ind:02d}"
        formatted = tools.format_source_content(source, src_id)
        formatted_sources.append(formatted)
    formatted_sources_str = "\n\n".join(formatted_sources)
    cur_date = tools.base_tools.current_datetime_string()
    instruction = dependencies.load_instruction("prompts/herald.md",
        articles=formatted_sources_str,
        user_request=herald_state["preferences"],
        current_date=cur_date,
        n_stories=herald_state["n_story"]
        )
    message = HumanMessage(content=instruction)
    llm_response = await llm.ainvoke([message], schema=state.Stories)
    return {
        "stories" : [story.model_dump() for story in llm_response.stories]
    }

async def extract_story(story_state : state.StoryWithContent) -> state.OutputState:
    content = []
    links = []
    news_parser = dependencies.get_article_parser()
    for article in story_state["related_articles"]:
        header = f"Source : {article["link"]}"
        fmt_article = await news_parser.get_story(article["link"])
        if fmt_article:
            links.append(article["link"])
            content.append(f"{header}\n {fmt_article}")
    if len(content) > 0:
        story : state.base_state.Story= {
            "title" : story_state["story"]["title"],
            "articles" : story_state["story"]["articles_id"],
            "content" : "\n".join(content),
            "links" : links,
            "published" : story_state["story"]["published"],
            "sections" : story_state["story"]["section"],
            "reason" : story_state["story"]["reason"]}
        return {"stories" : [story]}
    return {"stories" : []}
