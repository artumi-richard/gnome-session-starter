"""The session picker window: pick a session with Tab/Shift-Tab, launch it with Enter."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk, GLib

from . import config, potd
from .launch import launch_session
from .widgets import color_swatch, escape

_GRADIENT_CSS = b"""
window.session-starter {
    background-image: linear-gradient(160deg, #3584e4 0%, #1a5fb4 55%, #0b3a80 100%);
}
picture.potd-picture {
    border-radius: 0 12px 12px 0;
}
"""

# Size with the picture-of-the-day panel showing, and without it (list only).
# The windowed size never exceeds the "with picture" size in either dimension.
_SIZE_WITH_PICTURE = (1300, 700)
_LIST_WIDTH_WITH_PICTURE = 460
_SIZE_WITHOUT_PICTURE = (540, 630)


def _install_gradient_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(_GRADIENT_CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class PickerWindow(Adw.ApplicationWindow):
    def __init__(self, app, data):
        super().__init__(application=app, title="Launch Session")
        self.add_css_class("session-starter")
        self.data = data
        self.sessions = data["sessions"]

        self.toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        header.add_css_class("flat")
        self.toolbar_view.add_top_bar(header)

        # pack_end() inserts each new widget before the previous ones, so pack
        # the close button first to put it outermost (to the right of prefs).
        close_button = Gtk.Button(icon_name="window-close-symbolic")
        close_button.set_tooltip_text("Close")
        close_button.connect("clicked", lambda _b: self.get_application().quit())
        header.pack_end(close_button)

        prefs_button = Gtk.Button(icon_name="preferences-system-symbolic")
        prefs_button.set_tooltip_text("Preferences")
        prefs_button.connect("clicked", self.on_prefs_clicked)
        header.pack_end(prefs_button)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("boxed-list")
        self.listbox.set_margin_top(12)
        self.listbox.set_margin_bottom(12)
        self.listbox.set_margin_start(12)
        self.listbox.set_margin_end(12)
        self.listbox.connect("row-activated", self.on_row_activated)

        # Build the two possible content states once, up front, and just
        # switch between them on reload - creating fresh ScrolledWindow/
        # StatusPage wrappers each time and re-parenting self.listbox into
        # them is what caused the list to intermittently vanish (GTK4 won't
        # silently re-parent a widget that already has a parent).
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_child(self.listbox)
        self.scroller.set_vexpand(True)

        self.status_page = Adw.StatusPage(
            title="No sessions configured",
            description="Add a session in Preferences.",
            icon_name="preferences-system-symbolic",
        )

        self.stack = Gtk.Stack()
        self.stack.add_named(self.scroller, "sessions")
        self.stack.add_named(self.status_page, "empty")

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.content_box.append(self.stack)
        self.toolbar_view.set_content(self.content_box)

        self.set_content(self.toolbar_view)
        self.build_session_list()
        self._setup_picture_panel()

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        self.connect("map", self.on_map)

    def _setup_picture_panel(self):
        image_path = potd.cached_image_path()
        if image_path is not None:
            self.stack.set_hexpand(False)
            self.stack.set_size_request(_LIST_WIDTH_WITH_PICTURE, -1)

            picture = Gtk.Picture.new_for_filename(str(image_path))
            picture.set_content_fit(Gtk.ContentFit.COVER)
            picture.set_hexpand(True)
            picture.set_vexpand(True)
            picture.add_css_class("potd-picture")
            self.content_box.append(picture)

            self.set_default_size(*_SIZE_WITH_PICTURE)
            # "No bigger than 1040x522" - the simplest way to guarantee that
            # is to not let the window be resized past it.
            self.set_resizable(False)
        else:
            self.stack.set_hexpand(True)
            self.set_default_size(*_SIZE_WITHOUT_PICTURE)

        # Kick off a background fetch for tomorrow's picture, if today's
        # isn't already cached. This never blocks the window from showing
        # or quitting - it's a detached subprocess, not work done here.
        potd.request_refresh()

    def build_session_list(self):
        while (row := self.listbox.get_row_at_index(0)) is not None:
            self.listbox.remove(row)

        default_name = config.default_session_name(self.data)
        default_row = None
        for s in self.sessions:
            apps = s.get("apps", [])
            active = sum(1 for a in apps if (isinstance(a, dict) and a.get("active", True)) or isinstance(a, str))
            total = len(apps)
            subtitle = f"{active} app(s)" if active == total else f"{active} of {total} app(s)"
            row = Adw.ActionRow(title=escape(s["name"]))
            row.set_subtitle(subtitle)
            row.add_prefix(color_swatch(s.get("color")))
            if s["name"] == default_name:
                row.add_suffix(Gtk.Image(icon_name="starred-symbolic"))
                default_row = row
            row.session = s
            self.listbox.append(row)

        if not self.sessions:
            self.stack.set_visible_child_name("empty")
        else:
            self.stack.set_visible_child_name("sessions")
            if default_row is not None:
                self.listbox.select_row(default_row)

    def on_map(self, *_args):
        self.listbox.grab_focus()

    def on_prefs_clicked(self, _button):
        from .prefs import PreferencesWindow

        win = PreferencesWindow(self.get_application(), self.data)
        win.connect("close-request", lambda *_: self.reload_sessions())
        win.present()

    def reload_sessions(self):
        self.data = config.load()
        self.sessions = self.data["sessions"]
        self.build_session_list()
        self.listbox.grab_focus()

    def selected_index(self):
        row = self.listbox.get_selected_row()
        return row.get_index() if row else -1

    def select_index(self, index):
        n = len(self.sessions)
        if n == 0:
            return
        index %= n
        row = self.listbox.get_row_at_index(index)
        if row:
            self.listbox.select_row(row)
            row.grab_focus()

    def on_key_pressed(self, _controller, keyval, _keycode, state):
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        if keyval == Gdk.KEY_Escape:
            self.get_application().quit()
            return True

        if keyval in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab, Gdk.KEY_KP_Tab):
            current = self.selected_index()
            if current == -1:
                current = 0
            step = -1 if (shift or keyval == Gdk.KEY_ISO_Left_Tab) else 1
            self.select_index(current + step)
            return True

        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            row = self.listbox.get_selected_row()
            if row is not None:
                self.launch_and_quit(row.session)
            return True

        return False

    def on_row_activated(self, _listbox, row):
        self.launch_and_quit(row.session)

    def launch_and_quit(self, session):
        launch_session(session)
        self.get_application().quit()


class PickerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.artumi_richard.GnomeSessionStarter")
        self.window = None

    def do_activate(self):
        _install_gradient_css()
        data = config.load()
        if self.window is None:
            self.window = PickerWindow(self, data)
        self.window.present()


def main():
    app = PickerApp()
    return app.run(None)
