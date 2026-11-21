import pytest

from agents import agent
from tests.conftest import FakeModel
from tools import smart_home


@pytest.fixture(autouse=True)
def fresh_conversation(monkeypatch):
    monkeypatch.setattr(agent, "conversation_history", [])


def test_a_device_command_runs_the_smart_home_tool(read_device, monkeypatch):
    monkeypatch.setattr(
        agent,
        "model",
        FakeModel(
            'TOOL:control_device("the living room light" "turn on")',
            "The living room light is on now.",
        ),
    )
    monkeypatch.setattr(smart_home, "model", FakeModel("light1"))

    reply, tool_call, tool_result = agent.process_user_input("Turn on the living room light")

    assert reply == "The living room light is on now."
    assert tool_call == 'TOOL:control_device("the living room light" "turn on")'
    assert "state set to 'on'" in tool_result
    assert read_device("light1")["state"] == "on"


def test_several_tool_calls_in_one_request(read_device, monkeypatch):
    monkeypatch.setattr(
        agent,
        "model",
        FakeModel(
            'TOOL:control_device("light" "turn on")\nTOOL:control_device("door" "unlock")',
            "Done: the light is on and the back door is unlocked.",
        ),
    )
    monkeypatch.setattr(smart_home, "model", FakeModel("light1", "front door"))

    agent.process_user_input("Turn on the light and unlock the front door")

    assert read_device("light1")["state"] == "on"
    assert read_device("front door")["state"] == "unlocked"


def test_play_commands_go_straight_to_youtube(monkeypatch):
    model = FakeModel("Playing it for you.")
    monkeypatch.setattr(agent, "model", model)
    played = []
    monkeypatch.setattr(agent.youtube, "open_youtube", lambda query: played.append(query) or "ok")

    agent.process_user_input("play lofi beats")

    assert played == ["lofi beats"]
    assert len(model.prompts) == 1


def test_a_normal_question_is_answered_without_tools(monkeypatch):
    monkeypatch.setattr(agent, "model", FakeModel("Hello! How can I help?", "I'm fine, thanks."))

    reply, tool_call, tool_result = agent.process_user_input("How are you?")

    assert reply == "I'm fine, thanks."
    assert tool_call is None and tool_result is None


def test_the_conversation_is_remembered(monkeypatch):
    model = FakeModel("no tool", "Nice to meet you, Sam.", "no tool", "You are Sam.")
    monkeypatch.setattr(agent, "model", model)

    agent.process_user_input("My name is Sam")
    agent.process_user_input("What is my name?")

    assert "User: My name is Sam" in model.prompts[2]


@pytest.mark.parametrize(
    ("tool_call", "expected"),
    [
        ("TOOL:launch_rocket()", "Unknown tool."),
        ("TOOL:control_device(only_one_argument)", "control_device tool expects at least 2"),
        ("this is not a tool call", "Invalid tool call format."),
    ],
)
def test_impossible_or_broken_tool_calls_are_not_executed(tool_call, expected):
    [(call, result)] = agent.run_tool_from_call_multiple(tool_call)

    assert call == tool_call
    assert result.startswith(expected)
