from . import state
from .. import base_tools

def format_article_content(article: state.base_state.Article, id: str):
    return f"""### ARTICLE ID: {id} \n Title : {article["title"]} \n Published Date: {article["published"]}"""


def format_source_content(source : state.base_state.Source, src_id : str):
    articles = []
    for art_id, article in enumerate(source["articles"]):
        id = src_id + f"_{art_id:02d}"
        content = format_article_content(article, id)
        articles.append(content)
    return "\n\n".join(articles)




