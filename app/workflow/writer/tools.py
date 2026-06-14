from .. import base_state,base_tools

from typing import List

def _build_personas_str(story: base_state.Story, guests: List[base_state.Guest]) -> str:
    """
    Build the {personas} block for planner and writer prompts.
    Matches personas in story against guest configs by persona_id.
    """
    config_by_id = {g["persona_id"]: g["config"] for g in guests}
    lines = []
    historian = ""
    for persona in story["personas"]:
        pid = persona["persona_id"]
        config = config_by_id.get(pid, {})
        display = config.get("display_name", pid)
        line = f"""### {display} ({pid})\n
            ### Insight:\n{persona.get('insight', '')}"""
        if pid == "historian":
            historian = line
        else:
            lines.append(line)
    return "\n\n".join(lines), historian
