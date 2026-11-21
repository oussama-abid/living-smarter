import re
import shlex

import google.generativeai as genai

from config import settings
from prompts.prompts import general_chat_prompt, response_prompt, tool_instruction_prompt
from tools import smart_home, youtube
from tools.gmail_tool import get_today_email_count, send_email, summarize_last_n_emails
from tools.search_web_tool import SearchWebTool

genai.configure(api_key=settings.gemini_api_key)

model = genai.GenerativeModel(settings.gemini_model)

conversation_history = []


def decide_tool(user_input: str) -> str:
    ui_lower = user_input.lower().strip()
    if ui_lower.startswith("play "):
        query = user_input[5:].strip()
        if query:
            return f'TOOL:open_youtube("{query}")'

    context_for_tool = "\n".join(conversation_history[-6:])
    prompt = tool_instruction_prompt + "\n" + context_for_tool + f"\nUser: {user_input}\nAssistant:"
    response = model.generate_content(prompt)
    content = response.candidates[0].content.parts[0].text
    return content.strip()


def run_tool_from_call_multiple(tool_calls_text: str):
    results = []
    lines = [line.strip() for line in tool_calls_text.strip().splitlines() if line.strip()]
    pattern = r"^TOOL:(\w+)\((.*)\)$"

    for line in lines:
        match = re.match(pattern, line)
        if not match:
            results.append((line, "Invalid tool call format."))
            continue

        tool_name = match.group(1)
        args_str = match.group(2)

        try:
            args = shlex.split(args_str)
        except Exception as e:
            results.append((line, f"Failed to parse tool arguments: {e}"))
            continue

        if tool_name == "open_youtube":
            query = " ".join(args) if args else ""
            result = youtube.open_youtube(query)

        elif tool_name == "control_device":
            if len(args) < 2:
                result = (
                    "control_device tool expects at least 2 arguments: device_name_or_desc, action"
                )
            else:
                device_desc = args[0]
                action = args[1]
                result = smart_home.control_multiple_devices(device_desc, action)

        elif tool_name == "search_web":
            if len(args) != 1:
                result = "search_web tool expects 1 argument."
            else:
                tool = SearchWebTool(query=args[0])
                result = tool.run()

        elif tool_name == "send_email":
            if len(args) < 3:
                result = "send_email tool expects at least 3 arguments: to_email, subject, body"
            else:
                to_email = args[0]
                subject = args[1]
                body = args[2]
                from_email = args[3] if len(args) > 3 else None
                result = send_email(to_email, subject, body, from_email)

        elif tool_name == "get_today_email_count":
            result = get_today_email_count()

        elif tool_name == "summarize_last_n_emails":
            if len(args) != 1:
                result = "summarize_last_n_emails tool expects 1 argument: number of emails"
            else:
                try:
                    n = int(args[0])
                    result = summarize_last_n_emails(n)
                except ValueError:
                    result = "Argument must be an integer"

        elif tool_name == "check_email":
            if len(args) != 1:
                result = "check_email tool expects 1 argument."
            else:
                query = args[0]
                result = f"Checked email with query: {query}"

        else:
            result = "Unknown tool."

        results.append((line, result))
    return results


def generate_response(user_input: str, tool_call: str, tool_result: str) -> str:
    context_for_response = "\n".join(conversation_history[-6:])
    prompt = response_prompt.format(
        user_input=user_input, tool_call=tool_call, tool_result=tool_result
    )
    full_prompt = context_for_response + "\n" + prompt
    response = model.generate_content(full_prompt)
    content = response.candidates[0].content.parts[0].text
    return content.strip()


def process_user_input(user_input: str):
    global conversation_history

    conversation_history.append(f"User: {user_input}")

    tool_call_or_text = decide_tool(user_input)

    if tool_call_or_text.startswith("TOOL:"):
        tool_results = run_tool_from_call_multiple(tool_call_or_text)

        for tool_call, tool_result in tool_results:
            conversation_history.append(f"Assistant (tool_call): {tool_call}")
            conversation_history.append(f"Assistant (tool_result): {tool_result}")

        combined_tool_calls = "\n".join([tr[0] for tr in tool_results])
        combined_tool_results = "\n".join([str(tr[1]) for tr in tool_results])

        reply = generate_response(user_input, combined_tool_calls, combined_tool_results)
        conversation_history.append(f"Assistant: {reply}")

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        return reply, combined_tool_calls, combined_tool_results

    else:
        chat_response = model.generate_content(
            general_chat_prompt
            + "\n"
            + "\n".join(conversation_history[-6:])
            + f"\nUser: {user_input}\nAssistant:"
        )
        reply = chat_response.candidates[0].content.parts[0].text.strip()
        conversation_history.append(f"Assistant: {reply}")

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        return reply, None, None
