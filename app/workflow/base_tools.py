import json
from datetime import datetime
from app import dependencies
from .inquisitor.pipeline import get_pipeline as inquisitor
from . import base_state



def current_datetime_string() -> str:
    return datetime.now().strftime("%Y/%m/%d %H:%M")

def format_story(story : base_state.Story):
    fmt_head= f"### Title : {story["title"]} \n ### Published Date: {story["published"]}"
    fmt_body = f"### Content : {story.get("content", "")} \n ### Background Context: {story.get("context", "")}"
    fmt_story = fmt_head + "\n" + fmt_body
    return fmt_story

async def query_graph(query: str) -> str:
    """Queries the knowledge graph (read or write).
    Args:
        query: The Cypher query to execute. Embed all values directly 
               in the query string (e.g. MATCH (n:Person {name: 'Alice'})).
    Returns:
        JSON string of results for read queries, or a success/error message.
    """
    kb_client = dependencies.get_kb_client()
    try:
        result = await kb_client.execute_query(query)
        return json.dumps(result, indent=2, ensure_ascii=False) if result else "success"
    except Exception as e:
        return str(e)

def format_persona_config(config: dict) -> str:
    head = f"These are the config for only {config["name"]}, do not use any other config for it"
    def format_value(value, depth: int) -> str:
        indent = "\t" * depth
        if isinstance(value, dict):
            return format_dict(value, depth)
        if isinstance(value, bool):
            return str(value).lower()
        if value is None:
            return "null"
        if isinstance(value, str) and "\n" in value:
            lines = [f"{indent}>"]
            for line in value.splitlines():
                lines.append(f"{indent}\t{line}")
            return "\n".join(lines)
        return str(value)

    def format_dict(obj: dict, depth: int = 0) -> str:
        lines = []
        indent = "\t" * depth
        for key, value in obj.items():
            if isinstance(value, dict):
                lines.append(f"{indent}{key}:")
                lines.append(format_dict(value, depth + 1))
            else:
                formatted_value = format_value(value, depth + 1) if isinstance(value, str) and "\n" in str(value) else format_value(value, 0)
                if isinstance(value, str) and "\n" in value:
                    lines.append(f"{indent}{key}: {formatted_value}")
                else:
                    lines.append(f"{indent}{key}: {formatted_value}")
        return "\n".join(lines)

    return head + "\n" + format_dict(config)


async def search(query: str):
    """Returns formatted results based on the query
    
    Args :
    query : The query to search for

    Returns:
    Formatted result
    """
    inquisitor_graph = inquisitor()
    result = await inquisitor_graph.ainvoke({"query" : query})
    return result