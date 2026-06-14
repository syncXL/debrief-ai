from langchain_core.messages import SystemMessage
import json
from langchain_core.messages import ToolMessage,AIMessage

from app import dependencies
from . import state, tools


async def research_article(researcher_state: state.ResearcherState) -> state.ResearcherState:
    messages = researcher_state["messages"]
    # if len(messages) > 0:
    #     print(messages[-1])
    llm = dependencies.get_heavy_llm()
    if len(messages) == 0:
        prompt = dependencies.load_instruction("prompts/researcher.md",
                title=researcher_state["title"],
                content=researcher_state["content"])
        sys_msg = SystemMessage(content=prompt)
        messages = [sys_msg]

    response = await llm.ainvoke(messages, tools=tools.get_tools())
    print(type(response))
    return {"messages" : [response]}


def extract_tool_calls_with_results(research_state: state.ResearcherState):
    # Build a map of tool_call_id -> arguments from AIMessages
    args_map = {}
    for msg in research_state["messages"]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                args_map[tc["id"]] = tc["args"]

    # Pair each ToolMessage with its arguments
    results = []
    for msg in research_state["messages"]:
        if isinstance(msg, ToolMessage):
            results.append({
                "tool_name": msg.name,
                "args": args_map.get(msg.tool_call_id),
                "result": msg.content
            })
    return results

def add_context(researcher_state : state.ResearcherState) -> state.OutputState:
    messages = researcher_state["messages"]
    
    # Build tool_call_id -> args mapping directly
    args_map = {}
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                args_map[tc["id"]] = tc["args"]

    kb_contents = []
    if len(messages) == 0:
        return {"context" : ""}    
    
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_outp = json.loads(message.content)
            if tool_outp["add_to_kb"]:
                kb_content: state.AddToKB = {
                    "query": args_map.get(message.tool_call_id, {}).get("query"),
                    "content": tool_outp["new_context"],
                }
                kb_contents.append(kb_content)
    context = messages[-1].text
    return {"context" : context, "kb_contents" : kb_contents}    



    