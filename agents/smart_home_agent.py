import re
import shlex

from prompts.prompts import smarthome_instruction_prompt
from tools import smart_home


def decide_smart_home(user_input, conversation_history, model):
    context = "\n".join(conversation_history[-6:])
    prompt = smarthome_instruction_prompt + "\n" + context + f"\nUser: {user_input}\nAssistant:"
    response = model.generate_content(prompt)
    return response.candidates[0].content.parts[0].text.strip()


def run_smart_home(tool_call):
    pattern = r"SMARTHOME_TOOL:(\w+)\((.*)\)"
    match = re.match(pattern, tool_call.strip())
    if not match:
        return tool_call, "Invalid smart home tool call format."

    tool_name = match.group(1)
    args_str = match.group(2)

    try:
        args = shlex.split(args_str)
    except Exception as e:
        return tool_call, f"Failed to parse arguments: {e}"

    if tool_name == "control_device":
        if len(args) != 2:
            return tool_call, "control_device expects 2 arguments."
        return tool_call, smart_home.control_device(args[0], args[1])

    return tool_call, "Unknown smart home tool."
