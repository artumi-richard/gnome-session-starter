"""Session configuration storage: a JSON file of named sessions, each a list of commands."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "session-manager"
CONFIG_FILE = CONFIG_DIR / "sessions.json"


def default_config():
    return {"default_session": None, "sessions": []}


def load():
    if not CONFIG_FILE.exists():
        return default_config()
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
    data.setdefault("default_session", None)
    data.setdefault("sessions", [])
    return data


def save(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(CONFIG_FILE)


def get_session(data, name):
    for s in data["sessions"]:
        if s["name"] == name:
            return s
    return None


def default_session_name(data):
    name = data.get("default_session")
    if name and get_session(data, name):
        return name
    if data["sessions"]:
        return data["sessions"][0]["name"]
    return None
