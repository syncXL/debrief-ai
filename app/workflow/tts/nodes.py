from langchain_core.messages import HumanMessage
from app import dependencies
from . import state, tools

async def convert_to_ssml(ssml_state: state.base_state.Script) -> state.base_state.Script:
    llm = dependencies.get_max_llm()
    guest_str = "\n".join([
        tools.base_tools.format_persona_config(guest["config"])
        for guest in ssml_state["guests"]
    ])
    message = dependencies.load_instruction(
        "prompts/ssml_generator.md",
        node_type=ssml_state["script"]["node"],
        voice_configs=guest_str,
        transcript=ssml_state["script"]["sketch"]
    )
    response = await llm.ainvoke([HumanMessage(content=message)])
    ssml_state["script"]["script"] = response.text
    return {"script" : ssml_state["script"]}

async def synthesize_transcript(ssml_state: state.base_state.Script) -> state.Output:
    audio_generator = dependencies.get_tts()
    audio_storage = dependencies.get_storage()
    audio_data = await audio_generator.generate(ssml_state["script"]["script"])
    filename = tools.generate_filename(ssml_state["script"])
    if audio_data["state"] == "Success":
        audio_url = await audio_storage.upload(
            audio_data["audio"],filename
        )
        return {"audio_url" : audio_url, "transcript" : ssml_state["script"]["script"]}
    return {"audio_url" : "Failed"}
