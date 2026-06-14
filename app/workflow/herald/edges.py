from langgraph.types import Send
from . import state

def distribute_story(herald_state : state.HeraldState):
    payload = []
    n_story = herald_state["n_story"]
    for story in herald_state["stories"][:n_story]:
        articles = []
        for article_id in story["articles_id"]:
            src_id, art_id = article_id.split("_")
            src_id = int(src_id)
            art_id = int(art_id)
            article = herald_state["sources"][src_id]["articles"][art_id]
            articles.append(article)
        req = Send("extractor", {"story" : story, "related_articles" : articles})
        payload.append(req)
    return payload
