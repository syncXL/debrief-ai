from .. import base_tools
from .. import base_state

def generate_filename(trans: base_state.Transcript) -> str:
    ts = base_tools.current_datetime_string()
    return f"episode_{ts}_{trans["node"]}_{[trans["pos"]]}.mp3"