from agents.agent import process_user_input

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        reply, tool_call, tool_result = process_user_input(user_input)
        print(f"Assistant: {reply}")