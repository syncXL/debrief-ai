import json
import asyncio
import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .schemas import Episode
from app.workflow.pipelines import pipelines
from app.workflow.graph import build_graph
from app import dependencies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.post("/interpreter")
async def get_interpreter(body : dict):
    graph = pipelines.get("interpreter")
    return await graph.ainvoke(body)


@app.post("/archivist")
async def get_archivist(body : dict):
    graph = pipelines.get("archivist")
    return await graph.ainvoke(body)

@app.post("/herald")
async def get_herald(body : dict):
    graph = pipelines.get("herald")
    return await graph.ainvoke(body)

@app.post("/inquisitor")
async def get_inquisitor(body : dict):
    graph = pipelines.get("inquisitor")
    return await graph.ainvoke(body)

@app.post("/librarian")
async def get_librarian(body : dict):
    graph = pipelines.get("librarian")
    return await graph.ainvoke(body)

@app.post("/persona")
async def get_persona(body : dict):
    graph = pipelines.get("persona")
    return await graph.ainvoke(body)

@app.post("/researcher")
async def get_researcher(body : dict):
    graph = pipelines.get("researcher")
    return await graph.ainvoke(body)

@app.post("/show_router")
async def get_show_router(body : dict):
    graph = pipelines.get("show_router")
    return await graph.ainvoke(body)

@app.post("/tts")
async def get_tts(body : dict):
    graph = pipelines.get("tts")
    return await graph.ainvoke(body)

@app.post("/headliner")
async def get_headliner(body : dict):
    graph = pipelines.get("headliner")
    return await graph.ainvoke(body)

@app.post("/show_intro")
async def get_show_intro(body : dict):
    graph = pipelines.get("show_intro")
    return await graph.ainvoke(body)

@app.post("/conclude_show")
async def get_conclude_show(body : dict):
    graph = pipelines.get("conclude_show")
    return await graph.ainvoke(body)

@app.post("/show_segment")
async def get_show_segment(body : dict):
    graph = pipelines.get("show_segment")
    return await graph.ainvoke(body)

@app.post("/s2s")
async def get_s2s(body : dict):
    graph = pipelines.get("s2s")
    return await graph.ainvoke(body)

@app.post("/h2s")
async def get_h2s(body : dict):
    graph = pipelines.get("h2s")
    return await graph.ainvoke(body)

@app.post("/conclude_episode")
async def get_conclude_episode(body : dict):
    graph = pipelines.get("conclude_episode")
    return await graph.ainvoke(body)

@app.post("/generate-ep")
async def generate(body : Episode):
    graph = build_graph()
    return await graph.ainvoke({"preference" : body.preference})

async def run_archivist_for_kb(kb_content: dict):
    archivist = pipelines.get("archivist")
    try:
        await archivist.ainvoke({
            "context": kb_content["content"],
            "tool_caller": kb_content.get("query", ""),
        })
    except Exception as e:
        print(f"Archivist failed for kb_content: {e}")


async def episode_stream_generator(preference: str):
    graph = build_graph()
    ind = 0
    final_state: dict = {}

    async for state in graph.astream(
        {"preference": preference, "n_story": 10},
        stream_mode="values",
    ):
        final_state = state
        transcripts = {t["pos"]: t for t in state.get("transcripts", [])}

        # Drain every transcript that's ready (audio synthesized), in order
        while ind in transcripts and transcripts[ind].get("type") == 1 and transcripts[ind].get("url"):
            t = transcripts[ind]
            event = {
                "pos": t["pos"],
                "tag": t.get("node"),
                "audio_url": t["url"],
                "transcript": t.get("script", ""),
            }
            yield f"data: {json.dumps(event)}\n\n"
            ind += 1

    # Final flush — emit anything left over even if audio failed,
    # so the frontend gets full ordering and can decide how to handle nulls
    transcripts = {t["pos"]: t for t in final_state.get("transcripts", [])}
    while ind in transcripts:
        t = transcripts[ind]
        event = {
            "pos": t["pos"],
            "tag": t.get("tag"),
            "audio_url": t.get("url") or None,
            "transcript": t.get("script", ""),
        }
        yield f"data: {json.dumps(event)}\n\n"
        ind += 1

    yield f"data: {json.dumps({'type': 'done'})}\n\n"

    # Knowledge graph writes — parallel, fire-and-forget
    kb_contents = final_state.get("kb_contents", [])
    if kb_contents:
        asyncio.create_task(
            asyncio.gather(*[run_archivist_for_kb(kb) for kb in kb_contents], return_exceptions=True)
        )


@app.get("/stream")
async def stream_episode(
    preference: str = Query(...),
):
    return StreamingResponse(
        episode_stream_generator(preference),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


GRAPH_QUERY = """
MATCH (n)-[r]->(m)
RETURN elementId(n) AS source_id, labels(n) AS source_labels, properties(n) AS source_props,
       elementId(m) AS target_id, labels(m) AS target_labels, properties(m) AS target_props,
       type(r) AS rel_type
LIMIT 200
"""

@app.get("/graph")
async def get_graph():
    kb = dependencies.get_knowledge_base()
    rows = await kb.execute_query(GRAPH_QUERY)

    nodes = {}
    edges = []
    for row in rows:
        sid, tid = row["source_id"], row["target_id"]
        nodes[sid] = {
            "id": sid,
            "label": row["source_labels"][0] if row["source_labels"] else "Node",
            **row["source_props"],
        }
        nodes[tid] = {
            "id": tid,
            "label": row["target_labels"][0] if row["target_labels"] else "Node",
            **row["target_props"],
        }
        edges.append({"source": sid, "target": tid, "type": row["rel_type"]})

    return {"nodes": list(nodes.values()), "edges": edges}

# @app.get("/graph")
# async def get_graph():
#     driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
#     nodes, edges = {}, []
#     async with driver.session() as session:
#         result = await session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 200")
#         async for record in result:
#             n, r, m = record["n"], record["r"], record["m"]
#             nodes[n.element_id] = {"id": n.element_id, "label": list(n.labels)[0] if n.labels else "Node", **dict(n)}
#             nodes[m.element_id] = {"id": m.element_id, "label": list(m.labels)[0] if m.labels else "Node", **dict(m)}
#             edges.append({"source": n.element_id, "target": m.element_id, "type": r.type})
#     await driver.close()
#     return {"nodes": list(nodes.values()), "edges": edges}