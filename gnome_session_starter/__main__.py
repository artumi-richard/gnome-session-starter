import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw

from . import config


def run_prefs():
    from .prefs import PreferencesWindow

    app = Adw.Application(application_id="io.github.artumi_richard.GnomeSessionStarter.Preferences")

    def on_activate(a):
        data = config.load()
        win = PreferencesWindow(a, data)
        win.connect("close-request", lambda *_: a.quit())
        win.present()

    app.connect("activate", on_activate)
    return app.run(None)


def run_picker():
    from .picker import main

    return main()


def run_fetch_potd():
    from . import potd

    potd.fetch_and_store()
    return 0


def main():
    if "--fetch-potd" in sys.argv[1:]:
        return run_fetch_potd()
    if "--prefs" in sys.argv[1:] or "--preferences" in sys.argv[1:]:
        return run_prefs()
    return run_picker()


if __name__ == "__main__":
    sys.exit(main())
