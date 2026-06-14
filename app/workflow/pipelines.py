from .archivist.pipeline import get_pipeline as archivist_pipeline
from .herald.pipeline import get_pipeline as herald_pipeline
from .inquisitor.pipeline import get_pipeline as inquisitor_pipeline
from .interpreter.pipeline import get_pipeline as interpreter_pipeline
from .librarian.pipeline import get_pipeline as librarian_pipeline
from .persona.pipeline import get_pipeline as persona_pipeline
from .researcher.pipeline import get_pipeline as researcher_pipeline
from .show_router.pipeline import get_pipeline as show_router_pipeline
from .tts.pipeline import get_pipeline as tts_pipeline
from .writer import pipeline as writer_pipelines


pipelines = {
    "archivist": archivist_pipeline(),
    "herald": herald_pipeline(),
    "inquisitor": inquisitor_pipeline(),
    "interpreter": interpreter_pipeline(),
    "librarian": librarian_pipeline(),
    "persona": persona_pipeline(),
    "researcher": researcher_pipeline(),
    "show_router": show_router_pipeline(),
    "tts": tts_pipeline(),
    "headliner": writer_pipelines.build_headliner(),
    "show_intro" : writer_pipelines.write_show_intro(),
    "conclude_show" : writer_pipelines.conclude_show(),
    "show_segment" : writer_pipelines.write_show_segment(),
    "s2s" : writer_pipelines.write_s2s(),
    "h2s" : writer_pipelines.write_h2s(),
    "conclude_episode" : writer_pipelines.conclude_episode()
}