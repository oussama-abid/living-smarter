import pytest

from tests.conftest import FakeModel
from tools import smart_home


@pytest.mark.parametrize(
    ("action", "state"),
    [
        ("turn on", "on"),
        ("turn off", "off"),
        ("open", "open"),
        ("close", "closed"),
        ("lock", "locked"),
        ("unlock", "unlocked"),
        ("activate", "on"),
        ("deactivate", "off"),
        ("make it sparkle", None),
    ],
)
def test_normalize_action(action, state):
    assert smart_home.normalize_action(action) == state


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("set volume to 25", ("volume", 25)),
        ("set temperature to 21.5", ("value", 21.5)),
        ("brightness 80", ("value", 80)),
        ("turn on", (None, None)),
    ],
)
def test_extract_attribute_and_value(action, expected):
    assert smart_home.extract_attribute_and_value(action) == expected


def test_turn_on_a_light(read_device):
    result = smart_home.control_device("light1", "turn on")

    assert result == "Light1 updated: state set to 'on'."
    assert read_device("light1")["state"] == "on"


def test_names_are_matched_without_case(read_device):
    smart_home.control_device("Kitchen Light", "turn off")

    assert read_device("kitchen light")["state"] == "off"


def test_set_a_value(read_device):
    result = smart_home.control_device("living room tv", "set volume to 30")

    assert "volume set to 30" in result
    assert read_device("living room tv")["volume"] == 30


def test_unlock_a_door(read_device):
    smart_home.control_device("front door", "unlock")

    assert read_device("front door")["state"] == "unlocked"


def test_no_change_needed(read_device):
    assert smart_home.control_device("light1", "turn off") == "Light1 is already set as requested."


def test_unknown_device(devices_db):
    assert smart_home.control_device("toaster", "turn on") == "Device 'toaster' not found."


def test_control_multiple_devices_uses_the_devices_the_model_picked(read_device, monkeypatch):
    model = FakeModel("light1, light2")
    monkeypatch.setattr(smart_home, "model", model)

    result = smart_home.control_multiple_devices("all lights upstairs", "turn on")

    assert read_device("light1")["state"] == "on"
    assert read_device("light2")["state"] == "on"
    assert " | " in result
    assert "Name: light1, Type: light, Location: living room" in model.prompts[0]


def test_control_multiple_devices_without_a_match(devices_db, monkeypatch):
    monkeypatch.setattr(smart_home, "model", FakeModel(""))

    result = smart_home.control_multiple_devices("the spaceship", "turn on")

    assert result == "Sorry, I couldn't find any devices matching your request."
