import json

import pytest

from agents import agent
from evaluation.run import CASES_FILE, run_cases, score, tools_in, write_report
from tests.conftest import FakeModel
from tools import smart_home


def test_tools_are_read_from_the_tool_lines():
    calls = 'TOOL:control_device("light" "on")\nTOOL:send_email("a@b.c" "Hi" "Hello")'
    assert tools_in(calls) == ["control_device", "send_email"]
    assert tools_in(None) == []


@pytest.mark.parametrize(
    ("case", "tools", "passed"),
    [
        ({"expect": ["control_device"]}, ["control_device"], True),
        ({"expect": ["control_device"]}, [], False),
        ({"expect": ["control_device", "control_device"]}, ["control_device"], False),
        ({"expect": ["open_youtube"]}, ["open_youtube", "control_device"], True),
        ({"expect": [], "any_of": ["check_email", "get_today_email_count"]}, ["check_email"], True),
        ({"expect": [], "any_of": ["check_email"]}, [], False),
        ({"expect": []}, [], True),
        ({"expect": []}, ["send_email"], False),
        ({"expect": [], "allow": ["search_web"]}, ["search_web"], True),
    ],
)
def test_score(case, tools, passed):
    assert score(case, tools) is passed


def test_the_cases_file_is_valid():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))["cases"]

    assert len(cases) == 38
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert case["command"] and case["category"] and isinstance(case["expect"], list)


def test_a_run_never_sends_email_and_uses_its_own_database(devices_db, read_device, monkeypatch):
    # run_cases swaps the real tools for recorders: put the originals back afterwards
    for name in ("send_email", "get_today_email_count", "summarize_last_n_emails", "SearchWebTool"):
        monkeypatch.setattr(agent, name, getattr(agent, name))
    monkeypatch.setattr(agent.youtube, "open_youtube", agent.youtube.open_youtube)
    monkeypatch.setattr(agent, "conversation_history", [])
    monkeypatch.setattr(
        agent,
        "model",
        FakeModel(
            'TOOL:control_device("light" "turn on")\nTOOL:send_email("boss@example.com" "Sick" "Not coming")',
            "Done.",
        ),
    )
    monkeypatch.setattr(smart_home, "model", FakeModel("light1"))
    case = {
        "id": 1,
        "category": "multi-step",
        "command": "...",
        "expect": ["control_device", "send_email"],
    }

    [result] = run_cases([case], pause=0)

    assert result.passed
    assert read_device("light1")["state"] == "on"
    assert "Would send an email" in agent.send_email("boss@example.com", "Sick", "Not coming")
    assert "| 1 | multi-step |" in write_report([result], "fake-model")
