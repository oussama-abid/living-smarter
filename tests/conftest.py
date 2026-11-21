import os
import sqlite3
from types import SimpleNamespace

import pytest

# Settings are read when the app modules are imported: give them a fake key
# so the tests never need (or use) a real one.
os.environ["GEMINI_API_KEY"] = "test-key-not-real"

from db import device_db  # noqa: E402
from tools import smart_home  # noqa: E402


class FakeModel:
    """Stands in for a Gemini model: returns prepared replies, records the prompts."""

    def __init__(self, *replies: str):
        self.replies = list(replies)
        self.prompts: list[str] = []

    def generate_content(self, prompt: str):
        self.prompts.append(prompt)
        text = self.replies.pop(0)
        part = SimpleNamespace(text=text)
        candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]))
        return SimpleNamespace(candidates=[candidate])


@pytest.fixture
def devices_db(tmp_path, monkeypatch):
    """A fresh simulated smart home in a temporary SQLite file."""
    path = tmp_path / "devices.db"
    monkeypatch.setattr(device_db, "DB_PATH", path)
    monkeypatch.setattr(smart_home, "DB_PATH", path)
    device_db.init_db()
    device_db.insert_sample_devices()
    return path


@pytest.fixture
def read_device(devices_db):
    """Read one device's current state from the test database."""

    def read(name: str) -> dict:
        connection = sqlite3.connect(devices_db)
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM devices WHERE name = ?", (name,)).fetchone()
        connection.close()
        return dict(row)

    return read
