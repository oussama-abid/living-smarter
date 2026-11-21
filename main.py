from config import ConfigError

try:
    from agents.agent import process_user_input
    from db.device_db import init_db, insert_sample_devices
except ConfigError as error:
    raise SystemExit(f"Configuration error: {error}") from None


if __name__ == "__main__":
    init_db()
    insert_sample_devices()

    while True:
        user_input = input("You: ")
        try:
            reply, tool_call, tool_result = process_user_input(user_input)
        except ConfigError as error:
            print(f"Assistant: I can't do that yet. {error}")
            continue
        print(f"Assistant: {reply}")
