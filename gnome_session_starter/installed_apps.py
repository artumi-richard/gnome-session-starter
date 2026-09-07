"""List installed applications the same way GNOME's app grid does.

This is how you find the real launch command for something like a Steam
game (e.g. Dwarf Fortress) that shows up in GNOME's application list but
has no matching binary on $PATH: its .desktop entry's Exec= line often
runs it through something like `steam steam://rungameid/...` instead.
"""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio

from .desktop_entries import clean_exec


def list_installed_apps():
    """Return [{"name", "command", "icon"}] for every app that should_show()."""
    apps = []
    for info in Gio.AppInfo.get_all():
        if not info.should_show():
            continue
        commandline = info.get_commandline()
        if not commandline:
            continue
        name = info.get_display_name() or info.get_name()
        apps.append({
            "name": name,
            "command": clean_exec(commandline),
            "icon": info.get_icon(),
        })
    apps.sort(key=lambda a: a["name"].lower())
    return apps
