# The Debrief

An AI-powered multi-voice news podcast generator. Given a topic preference, it fetches live news, routes stories to specialist shows, generates per-persona spoken analysis, and streams back a full audio episode — each voice distinct, each segment structured as a broadcast segment.

## How it works

```
User preference → /stream (SSE)
  → interpreter       parse topic preference into structured query
  → librarian         fetch RSS sources matching the topic
  → herald            extract full article text and metadata
  → [per story]
      → researcher    query the knowledge graph for prior context
      → show_router   LLM selects 1–3 shows; deduplicates shared personas
      → personas      each persona generates its analysis in its own voice
      → historian     adds historical framing (World Affairs stories only)
  → [per show]
      → show_intro / show_segment / conclude_show   LLM-written broadcast copy
  → headliner         episode-level anchor reads
  → [per script, in order]
      → SSML generation   LLM converts transcript to Azure SSML markup
      → Azure TTS         synthesizes audio per persona voice
      → SSE event         streams audio URL to client as each segment completes
  → [fire-and-forget after stream]
      → archivist     extracts entities and relationships → writes to Neo4j
```

## Shows

Six specialist shows. Stories are routed to 1–3 shows per episode based on content. The Headliner and Historian are auto-assigned by the pipeline and are not selected by the router.

| Show | Section | Personas |
|---|---|---|
| Economy Today | Finance / Business / Markets | Economist, Banker |
| Political Pulse | Politics / Policy / Government | Politician, Lawyer |
| Science & Society | Health / Climate / Energy | Scientist, Economist |
| Tech Decoded | Technology / AI / Startups | Tech Analyst, Critic |
| The Socialite Report | Entertainment / Culture | Socialite, Politician |
| World Affairs | World / International | Geopolitician, Historian |

Personas that appear in multiple shows (Economist across Economy Today and Science & Society; Politician across Political Pulse and The Socialite Report) run once — their output is shared across both shows.

## Voices

Eleven distinct Azure Neural voices, one per persona:

| Persona | Voice |
|---|---|
| Headliner | en-US-EmmaNeural |
| Economist | en-GB-RyanNeural |
| Banker | en-US-DavisNeural |
| Politician | en-US-TonyNeural |
| Lawyer | en-GB-OliverNeural |
| Scientist | en-US-AriaNeural |
| Tech Analyst | en-US-BrianNeural |
| Critic | en-US-JasonNeural |
| Socialite | en-US-JennyNeural |
| Geopolitician | en-US-GuyNeural |
| Historian | en-GB-LibbyNeural |

Each persona config includes a tone map (rate, pitch, SSML style) per tone tag (`neutral`, `assertive`, `analytical`, `sharp`, etc.) and a list of supported Azure speech styles for expressive synthesis.

## Knowledge Graph

Every episode writes back to a Neo4j graph. The archivist pipeline runs after the stream completes, extracting named entities and relationships from the research context and writing structured Cypher.

**Node labels (temporal tiers):**
- Permanent: `Location`, `EventInstance`, `EventSeries`, `Concept/Ideology`, `Natural Resource`
- Conditional-temporal: `Person`, `Organisation`, `Government Body`, `Product/Technology`, `Project/Initiative`, `Financial Instrument`
- Temporal: `Role/Position`, `Policy/Law`, `Economic Indicator`, `Sanction/Restriction`, `Alliance/Coalition`, `Conflict/Crisis`

**Relationship types:** `HOLDS_POSITION`, `EMPLOYED_BY`, `OWNS_STAKE`, `INVESTED_IN`, `PARTICIPATED_IN`, `INSTANCE_OF`, `SANCTIONED_BY`, `IN_CONFLICT_WITH`, `ACCUSED_OF`, `CAUSED`, `RESPONDED_TO`, `SUPERSEDED_BY`, `REPRESENTS`, `ATTENDED`, `MERGED_WITH`, `AWARDED`, `RECEIVED_AID`, `HOSTED`, `REGULATES`, `FINED`

The graph is exposed via `GET /graph` for visualization.

## Stack

- **Runtime:** Python 3.13, [uv](https://github.com/astral-sh/uv)
- **API:** FastAPI + Server-Sent Events for episode streaming
- **Orchestration:** LangGraph (StateGraph)
- **LLM:** Azure OpenAI via LangChain
- **TTS:** Azure Cognitive Services Speech SDK (SSML multi-voice)
- **Knowledge graph:** Neo4j 5 (community)
- **Audio storage:** Cloudinary
- **Article extraction:** newspaper4k + lxml
- **Database:** PostgreSQL (SQLAlchemy + asyncpg)

## Running locally

Requires Docker and a `.env` file with credentials for Azure OpenAI, Azure Speech, Neo4j, Cloudinary, and PostgreSQL.

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`.

### Key endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/stream?preference=<topic>` | SSE stream — full episode generation |
| `POST` | `/generate-ep` | Non-streaming full episode (body: `{"preference": "..."}`) |
| `GET` | `/graph` | Neo4j knowledge graph (nodes + edges, limit 200) |
| `GET` | `/` | Health check |
| `POST` | `/interpreter` | Parse preference only |
| `POST` | `/show_router` | Route a story to shows only |
| `POST` | `/tts` | Synthesize a single transcript |

## Project layout

```
app/
  main.py              FastAPI app and SSE stream generator
  workflow/
    graph.py           Main LangGraph StateGraph
    nodes.py           Pipeline node functions
    edges.py           Conditional routing edges
    base_state.py      Shared state types
    base_tools.py      Shared tools (Neo4j query)
    show_router/       Show selection + persona dedup
    inquisitor/        Research agent (Neo4j query)
    archivist/         Knowledge graph writer
    tts/               SSML generation + Azure synthesis
    writer/            Broadcast copy writers (show, headliner, etc.)
  services/
    llm.py             Azure OpenAI provider
    tts.py             Azure TTS provider
    knowledge_base.py  Neo4j async client
    storage.py         Cloudinary upload
    news.py            RSS + article fetching
prompts/
  shows/               One config.yaml per show
  personas/            One config.yaml per persona (voice, tone map, styles)
  archivist/           Cypher read/write instructions and output schemas
  router.md            Show selection and persona dedup instructions
  ssml_generator.md    SSML template and tone mapping instructions
```