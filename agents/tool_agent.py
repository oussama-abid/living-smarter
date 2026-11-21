import re
import shlex

from prompts.prompts import tool_instruction_prompt
from tools import youtube
from tools.gmail_tool import get_today_email_count, send_email, summarize_last_n_emails
from tools.search_web_tool import SearchWebTool


def decide_tool(user_input, conversation_history, model):
    context = "\n".join(conversation_history[-6:])
    prompt = tool_instruction_prompt + "\n" + context + f"\nUser: {user_input}\nAssistant:"
    response = model.generate_content(prompt)
    return response.candidates[0].content.parts[0].text.strip()


def run_tool(tool_call):
    pattern = r"TOOL:(\w+)\((.*)\)"
    match = re.match(pattern, tool_call.strip())
    if not match:
        return tool_call, "Invalid tool call format."

    tool_name = match.group(1)
    args_str = match.group(2)

    try:
        args = shlex.split(args_str)
    except Exception as e:
        return tool_call, f"Failed to parse arguments: {e}"

    if tool_name == "open_youtube":
        query = " ".join(args) if args else ""
        return tool_call, youtube.open_youtube(query)

    elif tool_name == "search_web":
        if len(args) != 1:
            return tool_call, "search_web expects 1 argument."
        tool = SearchWebTool(query=args[0])
        return tool_call, tool.run()

    elif tool_name == "send_email":
        if len(args) < 3:
            return tool_call, "send_email expects at least 3 arguments."
        to_email, subject, body = args[0], args[1], args[2]
        from_email = args[3] if len(args) > 3 else None
        return tool_call, send_email(to_email, subject, body, from_email)

    elif tool_name == "get_today_email_count":
        count = get_today_email_count()
        return tool_call, count

    elif tool_name == "summarize_last_n_emails":
        if len(args) != 1:
            return tool_call, "summarize_last_n_emails expects 1 argument."
        try:
            n = int(args[0])
        except ValueError:
            return tool_call, "Argument must be an integer."
        summary = summarize_last_n_emails(n)
        return tool_call, summary

    elif tool_name == "check_email":
        if len(args) != 1:
            return tool_call, "check_email expects 1 argument."
        query = args[0]
        # Implement your email query logic here
        return tool_call, f"Email query result for: {query}"

    return tool_call, "Unknown tool."
