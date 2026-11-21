"""Rerun the paper's evaluation against the real Gemini models.

    uv run python -m evaluation.run
    uv run python -m evaluation.run --category multi-step --pause 15

Gemini makes every decision for real. Tools with side effects (email,
YouTube, web search) are replaced by recorders that only write down what
would have happened, and the smart home runs on a temporary database.
A run therefore sends no email and changes nothing outside this folder.

Each case is scored automatically: did the assistant call the tools the
command needs? The replies are saved too, so they can be reviewed by hand,
as in the paper.
"""

import argparse
import json
import re
import tempfile
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

CASES_FILE = Path(__file__).with_name("cases.json")
RESULTS_FILE = Path(__file__).with_name("results.md")
TOOL_NAME = re.compile(r"TOOL:(\w+)\(")


@dataclass
class Result:
    case: dict
    tools: list[str]
    reply: str
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and score(self.case, self.tools)


def tools_in(tool_calls: str | None) -> list[str]:
    """Names of the tools in the orchestrator's TOOL: lines, in order."""
    return TOOL_NAME.findall(tool_calls or "")


def score(case: dict, tools: list[str]) -> bool:
    """True when the called tools match what the command needs."""
    called = Counter(tools)
    for name, count in Counter(case["expect"]).items():
        if called[name] < count:
            return False
    any_of = case.get("any_of")
    if any_of and not any(called[name] for name in any_of):
        return False
    # Commands that need no tool: only the explicitly allowed ones may run
    if not case["expect"] and not any_of:
        allowed = set(case.get("allow", []))
        if any(name not in allowed for name in called):
            return False
    return True


def install_recorders(agent) -> None:
    """Replace tools that act on the outside world with harmless stand-ins."""

    def open_youtube(query=""):
        return f"[evaluation] Would open YouTube and play: {query}"

    def send_email(to_email, subject, body, from_email=None):
        return f"[evaluation] Would send an email to {to_email} with the subject '{subject}'."

    def get_today_email_count():
        return "[evaluation] You received 3 emails today: from Amazon, Manel and the university."

    def summarize_last_n_emails(n):
        return (
            f"[evaluation] Summary of the last {n} emails: Amazon says your order has shipped; "
            "Manel confirms the meeting at 16h; the university sent the exam schedule."
        )

    class RecordedSearch:
        def __init__(self, query):
            self.query = query

        def run(self):
            return f"[evaluation] Web search results for: {self.query}"

    agent.youtube.open_youtube = open_youtube
    agent.send_email = send_email
    agent.get_today_email_count = get_today_email_count
    agent.summarize_last_n_emails = summarize_last_n_emails
    agent.SearchWebTool = RecordedSearch


def use_temporary_smart_home(directory: Path) -> None:
    from db import device_db
    from tools import smart_home

    path = directory / "devices.db"
    device_db.DB_PATH = path
    smart_home.DB_PATH = path
    device_db.init_db()
    device_db.insert_sample_devices()


def run_cases(cases: list[dict], pause: float) -> list[Result]:
    from agents import agent

    install_recorders(agent)
    results = []
    category = None
    for case in cases:
        # One conversation per category, so follow-up commands have context
        if case["category"] != category:
            category = case["category"]
            agent.conversation_history = []
        print(f"[{case['id']:>2}] {case['command'][:70]}", flush=True)
        try:
            reply, tool_calls, _ = agent.process_user_input(case["command"])
            result = Result(case, tools_in(tool_calls), reply)
        except Exception as error:  # one failing case must not stop the run
            result = Result(case, [], "", error=f"{type(error).__name__}: {error}")
        print(f"     {'PASS' if result.passed else 'FAIL'}  tools: {result.tools or '-'}")
        results.append(result)
        if pause:
            time.sleep(pause)
    return results


def paper_task_done(case: dict) -> bool | None:
    """The hand-scored result from the paper, when the case has one."""
    return case.get("paper", {}).get("task_done")


def summary_rows(results: list[Result]) -> list[tuple[str, int, int, int]]:
    """Per category: (name, passed now, total, done in the paper)."""
    rows: dict[str, list[int]] = {}
    for result in results:
        row = rows.setdefault(result.case["category"], [0, 0, 0])
        row[0] += result.passed
        row[1] += 1
        row[2] += bool(paper_task_done(result.case))
    rows["all"] = [sum(row[i] for row in rows.values()) for i in range(3)]
    return [(name, passed, total, paper) for name, (passed, total, paper) in rows.items()]


def _cell(text: str, limit: int = 220) -> str:
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _mark(value: bool | None) -> str:
    return {True: "✅", False: "❌", None: "-"}[value]


def write_report(results: list[Result], model: str) -> str:
    lines = [
        "# Evaluation results",
        "",
        f"Run on {datetime.now():%Y-%m-%d %H:%M} with `{model}`. "
        "Scored automatically on tool selection; review the replies by hand for answer quality.",
        "",
        "| Category | Correct tools now | Task done in the paper |",
        "|---|---|---|",
    ]
    for name, passed, total, paper in summary_rows(results):
        lines.append(
            f"| {name} | {passed} / {total} ({passed / total:.0%}) "
            f"| {paper} / {total} ({paper / total:.0%}) |"
        )
    lines += [
        "",
        "| # | Category | Command | Expected | Called | Now | Paper | Reply |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        expected = ", ".join(r.case["expect"]) or "-"
        if r.case.get("any_of"):
            expected += " (any of: " + ", ".join(r.case["any_of"]) + ")"
        lines.append(
            f"| {r.case['id']} | {r.case['category']} | {_cell(r.case['command'], 90)} | "
            f"{expected} | {', '.join(r.tools) or '-'} | {'✅' if r.passed else '❌'} | "
            f"{_mark(paper_task_done(r.case))} | {_cell(r.error or r.reply)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--category", help="run only one category, e.g. multi-step")
    parser.add_argument(
        "--pause", type=float, default=10, help="seconds between cases (free-tier rate limit)"
    )
    args = parser.parse_args()

    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))["cases"]
    if args.category:
        cases = [case for case in cases if case["category"] == args.category]

    try:
        from config import settings
    except RuntimeError as error:  # config.ConfigError, raised while the settings load
        raise SystemExit(f"Configuration error: {error}") from None

    with tempfile.TemporaryDirectory() as directory:
        use_temporary_smart_home(Path(directory))
        results = run_cases(cases, args.pause)

    report = write_report(results, settings.gemini_model)
    RESULTS_FILE.write_text(report, encoding="utf-8")
    print()
    print(f"{'category':<15} {'now':>9}   {'paper':>9}")
    for name, passed, total, paper in summary_rows(results):
        print(
            f"{name:<15} {passed:>2} / {total:<2} {passed / total:>4.0%}   {paper:>2} / {total:<2} {paper / total:>4.0%}"
        )
    print(f"\nFull results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
