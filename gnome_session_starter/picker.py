"""The session picker window: pick a session with Tab/Shift-Tab, launch it with Enter."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk, GLib

from . import config
from .launch import launch_session


class PickerWindow(Adw.ApplicationWindow):
    def __init__(self, app, data):
        super().__init__(application=app, title="Launch Session")
        self.set_default_size(360, 420)
        self.data = data
        self.sessions = data["sessions"]

        self.toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
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

        self.set_content(self.toolbar_view)
        self.build_session_list()

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        self.connect("map", self.on_map)

    def build_session_list(self):
        while (row := self.listbox.get_row_at_index(0)) is not None:
            self.listbox.remove(row)

        default_name = config.default_session_name(self.data)
        default_row = None
        for s in self.sessions:
            row = Adw.ActionRow(title=s["name"])
            row.set_subtitle(f"{len(s.get('apps', []))} app(s)")
            row.session = s
            if s["name"] == default_name:
                row.add_css_class("accent")
                default_row = row
            self.listbox.append(row)

        if not self.sessions:
            status = Adw.StatusPage(
                title="No sessions configured",
                description="Add a session in Preferences.",
                icon_name="preferences-system-symbolic",
            )
            self.toolbar_view.set_content(status)
        else:
            scroller = Gtk.ScrolledWindow()
            scroller.set_child(self.listbox)
            scroller.set_vexpand(True)
            self.toolbar_view.set_content(scroller)
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
        data = config.load()
        if self.window is None:
            self.window = PickerWindow(self, data)
        self.window.present()


def main():
    app = PickerApp()
    return app.run(None)
