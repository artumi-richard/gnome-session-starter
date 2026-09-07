"""Read GNOME's Startup Applications list (~/.config/autostart/*.desktop)."""
import configparser
import os
from pathlib import Path

from .desktop_entries import clean_exec

AUTOSTART_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart"


def list_entries():
    """Return [{"name": ..., "command": ...}] for enabled user autostart entries."""
    entries = []
    if not AUTOSTART_DIR.is_dir():
        return entries

    for path in sorted(AUTOSTART_DIR.glob("*.desktop")):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except configparser.Error:
            continue
        if "Desktop Entry" not in parser:
            continue
        section = parser["Desktop Entry"]

        if section.get("Hidden", "false").lower() == "true":
            continue
        if section.get("X-GNOME-Autostart-enabled", "true").lower() == "false":
            continue

        exec_value = section.get("Exec", "").strip()
        if not exec_value:
            continue

        name = section.get("Name", "").strip() or path.stem
        entries.append({"name": name, "command": clean_exec(exec_value)})

    return entries
