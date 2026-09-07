"""Small shared GTK widget helpers."""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk

_provider = Gtk.CssProvider()
_provider_installed = False
_registered_colors = set()


def _ensure_provider_installed():
    global _provider_installed
    if _provider_installed:
        return
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), _provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    _provider_installed = True


def _register_color(hex_color):
    _ensure_provider_installed()
    if hex_color in _registered_colors:
        return
    _registered_colors.add(hex_color)
    rules = [".session-swatch { border-radius: 4px; }"]
    rules += [
        f".session-swatch-{c.lstrip('#')} {{ background-color: {c}; }}"
        for c in _registered_colors
    ]
    _provider.load_from_data("\n".join(rules).encode())


def color_swatch(hex_color, size=14):
    """A small rounded square filled with hex_color, for use as a row prefix/suffix."""
    hex_color = hex_color or "#3584e4"
    _register_color(hex_color)

    box = Gtk.Box()
    box.set_size_request(size, size)
    box.set_valign(Gtk.Align.CENTER)
    box.add_css_class("session-swatch")
    box.add_css_class(f"session-swatch-{hex_color.lstrip('#')}")
    return box
