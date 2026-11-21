import sqlite3
from datetime import datetime

from config import settings

DB_PATH = settings.database_path

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            state TEXT DEFAULT 'off',
            value REAL,
            volume INTEGER,
            unit TEXT,
            location TEXT,
            last_updated TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Device database initialized.")

def insert_sample_devices():
    sample_devices = [
        # Lights
        ("light1", "light", "off", 0, None, "%", "living room", "2025-06-26 14:00:00"),
        ("light2", "light", "off", 0, None, "%", "bedroom", "2025-06-26 14:00:00"),
        ("kitchen light", "light", "on", 75, None, "%", "kitchen", "2025-06-26 14:00:00"),
        ("bathroom light", "light", "on", 60, None, "%", "bathroom", "2025-06-26 14:00:00"),
        ("hallway light", "light", "off", 0, None, "%", "hallway", "2025-06-26 14:00:00"),

        # TVs
        ("living room tv", "tv", "on", None, 12, "volume", "living room", "2025-06-26 14:00:00"),
        ("bedroom tv", "tv", "off", None, 0, "volume", "bedroom", "2025-06-26 14:00:00"),
        ("kitchen tv", "tv", "off", None, 0, "volume", "kitchen", "2025-06-26 14:00:00"),

        # Thermostats / Temperature
        ("hall thermostat", "thermostat", "on", 22.0, None, "°C", "hallway", "2025-06-26 14:00:00"),
        ("bedroom thermostat", "thermostat", "off", 19.5, None, "°C", "bedroom", "2025-06-26 14:00:00"),
        ("garage thermostat", "thermostat", "on", 17.0, None, "°C", "garage", "2025-06-26 14:00:00"),

        # AC Units
        ("living room ac", "ac", "on", 21.0, None, "°C", "living room", "2025-06-26 14:00:00"),
        ("bedroom ac", "ac", "off", 23.5, None, "°C", "bedroom", "2025-06-26 14:00:00"),

        # Cameras
        ("front door camera", "camera", "on", None, None, None, "entrance", "2025-06-26 14:00:00"),
        ("garage camera", "camera", "on", None, None, None, "garage", "2025-06-26 14:00:00"),
        ("backyard camera", "camera", "off", None, None, None, "backyard", "2025-06-26 14:00:00"),

        # Doors
        ("garage door", "door", "closed", None, None, None, "garage", "2025-06-26 14:00:00"),
        ("front door", "door", "locked", None, None, None, "entrance", "2025-06-26 14:00:00"),
        ("back door", "door", "unlocked", None, None, None, "backyard", "2025-06-26 14:00:00"),

        # Speakers
        ("kitchen speaker", "speaker", "on", None, 40, "dB", "kitchen", "2025-06-26 14:00:00"),
        ("bedroom speaker", "speaker", "off", None, 0, "dB", "bedroom", "2025-06-26 14:00:00"),
        ("garage speaker", "speaker", "on", None, 20, "dB", "garage", "2025-06-26 14:00:00"),

        # Smart Plugs
        ("coffee machine plug", "plug", "off", None, None, None, "kitchen", "2025-06-26 14:00:00"),
        ("gaming pc plug", "plug", "on", None, None, None, "living room", "2025-06-26 14:00:00"),
        ("vacuum plug", "plug", "off", None, None, None, "hallway", "2025-06-26 14:00:00"),

        # Appliances
        ("bathroom heater", "heater", "off", 0, None, "°C", "bathroom", "2025-06-26 14:00:00"),
        ("washing machine", "appliance", "off", None, None, None, "laundry", "2025-06-26 14:00:00"),
        ("dryer", "appliance", "off", None, None, None, "laundry", "2025-06-26 14:00:00"),
        ("dishwasher", "appliance", "off", None, None, None, "kitchen", "2025-06-26 14:00:00"),

        # Curtains / Blinds
        ("living room blinds", "blinds", "closed", None, None, None, "living room", "2025-06-26 14:00:00"),
        ("bedroom curtains", "blinds", "open", None, None, None, "bedroom", "2025-06-26 14:00:00"),

        # Humidifiers
        ("bedroom humidifier", "humidifier", "on", 45, None, "%", "bedroom", "2025-06-26 14:00:00"),

        # Air Purifiers
        ("hallway air purifier", "air_purifier", "on", 3, None, "level", "hallway", "2025-06-26 14:00:00"),

        # Sensors
        ("smoke detector", "sensor", "on", None, None, None, "kitchen", "2025-06-26 14:00:00"),
        ("motion sensor", "sensor", "on", None, None, None, "backyard", "2025-06-26 14:00:00"),

        # Fridge & Oven
        ("fridge", "appliance", "on", 4, None, "°C", "kitchen", "2025-06-26 14:00:00"),
        ("oven", "appliance", "off", 0, None, "°C", "kitchen", "2025-06-26 14:00:00")
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for device in sample_devices:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO devices 
                (name, type, state, value, volume, unit, location, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, device)
        except Exception as e:
            print(f"❌ Failed to insert {device[0]}: {e}")

    conn.commit()
    conn.close()
    print("✅ 40+ Sample smart home devices inserted.")
