import re
import sqlite3
from datetime import datetime

import google.generativeai as genai

from config import settings

DB_PATH = settings.database_path

genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_helper_model)

# Map various user actions to normalized device states
ACTION_TO_STATE = {
    "on": "on",
    "off": "off",
    "open": "open",
    "close": "closed",
    "lock": "locked",
    "unlock": "unlocked",
    "start": "on",
    "stop": "off",
    "turn on": "on",
    "turn off": "off",
    "activate": "on",
    "deactivate": "off",
}


def normalize_action(action):
    action = action.lower()
    for key in ACTION_TO_STATE:
        if key in action:
            return ACTION_TO_STATE[key]
    return None


def extract_attribute_and_value(action: str):
    """
    Extract numeric attribute (volume, temperature, etc.) and value from action string.
    Returns (attribute_name, value) or (None, None) if none found.
    """
    match = re.search(
        r"(volume|temperature|value|level|brightness|speed|humidity|temp)[^\d\-\.]*([\d\.\-]+)",
        action,
        re.I,
    )
    if not match:
        return None, None

    attr = match.group(1).lower()
    val_str = match.group(2)
    try:
        val = int(val_str)
    except ValueError:
        try:
            val = float(val_str)
        except ValueError:
            val = val_str  # fallback to string if parsing fails

    # Normalize attribute name variants
    if attr in ["temperature", "temp", "level", "humidity", "brightness", "speed"]:
        attr = "value"

    return attr, val


def get_all_devices():
    """Return all devices with name, type, and location."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, type, location FROM devices")
    devices = cursor.fetchall()  # List of tuples (name, type, location)
    conn.close()
    return devices


def control_device(device_name, action):
    """Control a single device by exact name."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, type, state, value, volume, unit FROM devices WHERE LOWER(name)=?",
        (device_name.lower(),),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return f"Device '{device_name}' not found."

    name, dev_type, state, value, volume, unit = row

    new_state = normalize_action(action)
    attr, attr_val = extract_attribute_and_value(action)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    updates = []
    params = []

    # Update state if changed
    if new_state and new_state != state:
        updates.append("state=?")
        params.append(new_state)
    else:
        new_state = state

    # Update attribute values if present and changed
    if attr and attr_val is not None:
        if attr == "volume" and volume != attr_val:
            updates.append("volume=?")
            params.append(attr_val)
        elif attr == "value" and value != attr_val:
            updates.append("value=?")
            params.append(attr_val)

    if not updates:
        conn.close()
        return f"{name.capitalize()} is already set as requested."

    # Update last_updated timestamp
    updates.append("last_updated=?")
    params.append(now)

    sql = f"UPDATE devices SET {', '.join(updates)} WHERE LOWER(name)=?"
    params.append(device_name.lower())

    cursor.execute(sql, params)
    conn.commit()
    conn.close()

    # Prepare confirmation message
    msg_parts = []
    if "state=?" in updates:
        msg_parts.append(f"state set to '{new_state}'")
    if "volume=?" in updates:
        msg_parts.append(f"volume set to {attr_val}")
    if "value=?" in updates:
        msg_parts.append(f"value set to {attr_val}")

    msg = ", ".join(msg_parts)
    return f"{name.capitalize()} updated: {msg}."


def control_multiple_devices(user_command: str, action: str):
    """
    Uses Gemini to parse user_command, find matching devices from all devices,
    and control each one accordingly.
    """
    devices = get_all_devices()
    if not devices:
        return "No devices found in the system."

    # Prepare device info for Gemini prompt
    devices_info = "\n".join(
        [f"Name: {name}, Type: {typ}, Location: {loc}" for (name, typ, loc) in devices]
    )

    prompt = f"""
You are a smart home assistant helping to control devices.

Here is the list of devices available:
{devices_info}

User command: "{user_command}"

Return ONLY a list of device NAMES that the user command refers to.
Separate device names by commas, with no additional explanation.
"""

    response = model.generate_content(prompt)
    device_names_text = response.candidates[0].content.parts[0].text.strip()

    device_names = [d.strip() for d in device_names_text.split(",") if d.strip()]

    if not device_names:
        return "Sorry, I couldn't find any devices matching your request."

    # Control each device and collect results
    results = []
    for device_name in device_names:
        res = control_device(device_name, action)
        results.append(res)

    return " | ".join(results)
