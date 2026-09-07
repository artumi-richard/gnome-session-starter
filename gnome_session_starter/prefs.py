"""Preferences window: configure sessions and the apps each one launches."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from . import autostart, config
from .widgets import color_swatch


class PreferencesWindow(Adw.Window):
    def __init__(self, app, data):
        super().__init__(application=app, title="Session Manager Preferences")
        self.set_default_size(1080, 720)
        self.data = data
        self.current_session = None
        self._updating_color_button = False

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        split = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        split.set_position(220)
        toolbar_view.set_content(split)
        self.set_content(toolbar_view)

        # --- Left: list of sessions ---
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.session_listbox = Gtk.ListBox()
        self.session_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.session_listbox.add_css_class("navigation-sidebar")
        self.session_listbox.connect("row-selected", self.on_session_selected)

        left_scroller = Gtk.ScrolledWindow()
        left_scroller.set_child(self.session_listbox)
        left_scroller.set_vexpand(True)
        left_box.append(left_scroller)

        session_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        session_toolbar.set_margin_top(6)
        session_toolbar.set_margin_bottom(6)
        session_toolbar.set_margin_start(6)
        session_toolbar.set_margin_end(6)
        add_session_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_session_btn.set_tooltip_text("Add session")
        add_session_btn.connect("clicked", self.on_add_session)
        copy_session_btn = Gtk.Button(icon_name="edit-copy-symbolic")
        copy_session_btn.set_tooltip_text("Duplicate session")
        copy_session_btn.connect("clicked", self.on_copy_session)
        remove_session_btn = Gtk.Button(icon_name="list-remove-symbolic")
        remove_session_btn.set_tooltip_text("Delete session")
        remove_session_btn.connect("clicked", self.on_remove_session)
        session_toolbar.append(add_session_btn)
        session_toolbar.append(copy_session_btn)
        session_toolbar.append(remove_session_btn)
        left_box.append(session_toolbar)

        split.set_start_child(left_box)

        # --- Right: session detail ---
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_box.set_margin_top(12)
        right_box.set_margin_bottom(12)
        right_box.set_margin_start(12)
        right_box.set_margin_end(12)

        name_row = Adw.EntryRow(title="Session name")
        name_row.connect("changed", self.on_name_changed)
        self.name_row = name_row
        name_group = Adw.PreferencesGroup()
        name_group.add(name_row)
        right_box.append(name_group)

        self.default_check = Gtk.CheckButton(label="Use as default session (launch on Enter)")
        self.default_check.connect("toggled", self.on_default_toggled)
        right_box.append(self.default_check)

        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        color_box.append(Gtk.Label(label="Color"))
        self.color_button = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog())
        self.color_button.connect("notify::rgba", self.on_color_changed)
        color_box.append(self.color_button)
        right_box.append(color_box)

        apps_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        apps_label = Gtk.Label(label="Applications to launch", halign=Gtk.Align.START, hexpand=True)
        apps_label.add_css_class("heading")
        apps_header.append(apps_label)
        import_btn = Gtk.Button(label="Import from Startup Applications…")
        import_btn.connect("clicked", self.on_import_clicked)
        apps_header.append(import_btn)
        right_box.append(apps_header)

        self.app_listbox = Gtk.ListBox()
        self.app_listbox.add_css_class("boxed-list")
        app_scroller = Gtk.ScrolledWindow()
        app_scroller.set_child(self.app_listbox)
        app_scroller.set_vexpand(True)
        right_box.append(app_scroller)

        app_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.app_entry = Gtk.Entry(hexpand=True)
        self.app_entry.set_placeholder_text("Command to launch, e.g. firefox or steam")
        self.app_entry.connect("activate", self.on_add_app)
        add_app_btn = Gtk.Button(label="Add")
        add_app_btn.connect("clicked", self.on_add_app)
        app_entry_box.append(self.app_entry)
        app_entry_box.append(add_app_btn)
        right_box.append(app_entry_box)

        self.right_box = right_box
        right_box.set_sensitive(False)
        split.set_end_child(right_box)

        self.refresh_session_list()

    # --- session list management ---

    def refresh_session_list(self, select_name=None):
        self.session_listbox.remove_all()
        default_name = self.data.get("default_session")
        row_to_select = None
        for s in self.data["sessions"]:
            row = Adw.ActionRow(title=s["name"])
            if s["name"] == default_name:
                row.set_subtitle("Default")
            row.add_prefix(color_swatch(s.get("color")))
            row.session = s
            self.session_listbox.append(row)
            if s["name"] == select_name:
                row_to_select = row
        if row_to_select is None and self.data["sessions"]:
            row_to_select = self.session_listbox.get_row_at_index(0)
        if row_to_select is not None:
            self.session_listbox.select_row(row_to_select)
        else:
            self.current_session = None
            self.right_box.set_sensitive(False)

    def on_add_session(self, _button):
        name = self._unique_name("New Session")
        color = config.color_for_index(len(self.data["sessions"]))
        session = {"name": name, "apps": [], "color": color}
        self.data["sessions"].append(session)
        if self.data.get("default_session") is None:
            self.data["default_session"] = name
        config.save(self.data)
        self.refresh_session_list(select_name=name)

    def on_copy_session(self, _button):
        if self.current_session is None:
            return
        name = self._unique_name(f"{self.current_session['name']} copy")
        copy = {
            "name": name,
            "apps": list(self.current_session.get("apps", [])),
            "color": self.current_session.get("color", config.color_for_index(len(self.data["sessions"]))),
        }
        self.data["sessions"].append(copy)
        config.save(self.data)
        self.refresh_session_list(select_name=name)

    def on_remove_session(self, _button):
        if self.current_session is None:
            return
        name = self.current_session["name"]

        dialog = Adw.AlertDialog(
            heading="Delete session?",
            body=f"“{name}” and its list of apps will be permanently deleted. This can't be undone.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_remove_session_response, name)
        dialog.present(self)

    def _on_remove_session_response(self, _dialog, response, name):
        if response != "delete":
            return
        self.data["sessions"] = [s for s in self.data["sessions"] if s["name"] != name]
        if self.data.get("default_session") == name:
            self.data["default_session"] = (
                self.data["sessions"][0]["name"] if self.data["sessions"] else None
            )
        config.save(self.data)
        self.refresh_session_list()

    def _unique_name(self, base):
        existing = {s["name"] for s in self.data["sessions"]}
        if base not in existing:
            return base
        i = 2
        while f"{base} {i}" in existing:
            i += 1
        return f"{base} {i}"

    def on_session_selected(self, _listbox, row):
        if row is None:
            self.current_session = None
            self.right_box.set_sensitive(False)
            return
        self.current_session = row.session
        self.right_box.set_sensitive(True)
        self.name_row.set_text(self.current_session["name"])
        self.default_check.set_active(
            self.data.get("default_session") == self.current_session["name"]
        )
        rgba = Gdk.RGBA()
        rgba.parse(self.current_session.get("color", config.color_for_index(0)))
        self._updating_color_button = True
        self.color_button.set_rgba(rgba)
        self._updating_color_button = False
        self.refresh_app_list()

    # --- session detail: name / default ---

    def on_name_changed(self, entry):
        if self.current_session is None:
            return
        new_name = entry.get_text().strip()
        if not new_name or new_name == self.current_session["name"]:
            return
        old_name = self.current_session["name"]
        if any(s["name"] == new_name for s in self.data["sessions"] if s is not self.current_session):
            return  # avoid duplicate names while user is still typing
        self.current_session["name"] = new_name
        if self.data.get("default_session") == old_name:
            self.data["default_session"] = new_name
        config.save(self.data)
        # Update the sidebar row in place instead of rebuilding the list, so we
        # don't reselect it and re-set the entry's text (which would reset the
        # cursor and steal focus on every keystroke).
        row = self.session_listbox.get_selected_row()
        if row is not None:
            row.set_title(new_name)

    def on_default_toggled(self, check):
        if self.current_session is None:
            return
        if check.get_active():
            self.data["default_session"] = self.current_session["name"]
        elif self.data.get("default_session") == self.current_session["name"]:
            self.data["default_session"] = None
        config.save(self.data)
        self.refresh_session_list(select_name=self.current_session["name"])

    def on_color_changed(self, button, _pspec):
        if self.current_session is None or self._updating_color_button:
            return
        rgba = button.get_rgba()
        hex_color = "#{:02x}{:02x}{:02x}".format(
            round(rgba.red * 255), round(rgba.green * 255), round(rgba.blue * 255)
        )
        self.current_session["color"] = hex_color
        config.save(self.data)
        self.refresh_session_list(select_name=self.current_session["name"])

    # --- session detail: apps ---

    def refresh_app_list(self):
        self.app_listbox.remove_all()
        if self.current_session is None:
            return
        for i, app in enumerate(self.current_session.get("apps", [])):
            row = Adw.ActionRow(title=app)
            up_btn = Gtk.Button(icon_name="go-up-symbolic", valign=Gtk.Align.CENTER)
            up_btn.add_css_class("flat")
            up_btn.connect("clicked", self.on_move_app, i, -1)
            down_btn = Gtk.Button(icon_name="go-down-symbolic", valign=Gtk.Align.CENTER)
            down_btn.add_css_class("flat")
            down_btn.connect("clicked", self.on_move_app, i, 1)
            remove_btn = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
            remove_btn.add_css_class("flat")
            remove_btn.connect("clicked", self.on_remove_app, i)
            row.add_suffix(up_btn)
            row.add_suffix(down_btn)
            row.add_suffix(remove_btn)
            self.app_listbox.append(row)

    def on_add_app(self, _widget):
        if self.current_session is None:
            return
        cmd = self.app_entry.get_text().strip()
        if not cmd:
            return
        self.current_session.setdefault("apps", []).append(cmd)
        self.app_entry.set_text("")
        config.save(self.data)
        self.refresh_app_list()

    def on_remove_app(self, _button, index):
        apps = self.current_session.get("apps", [])
        if 0 <= index < len(apps):
            del apps[index]
            config.save(self.data)
            self.refresh_app_list()

    def on_move_app(self, _button, index, delta):
        apps = self.current_session.get("apps", [])
        new_index = index + delta
        if 0 <= new_index < len(apps):
            apps[index], apps[new_index] = apps[new_index], apps[index]
            config.save(self.data)
            self.refresh_app_list()

    def on_import_clicked(self, _button):
        if self.current_session is None:
            return
        entries = autostart.list_entries()
        existing = set(self.current_session.get("apps", []))

        dialog = Adw.Window(
            application=self.get_application(),
            transient_for=self,
            modal=True,
            title="Import from Startup Applications",
        )
        dialog.set_default_size(420, 400)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)
        dialog.set_content(toolbar_view)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)

        if not entries:
            content.append(Adw.StatusPage(
                title="Nothing to import",
                description="No enabled entries found in Startup Applications.",
            ))
        else:
            listbox = Gtk.ListBox()
            listbox.add_css_class("boxed-list")
            checks = []
            for e in entries:
                row = Adw.ActionRow(title=e["name"], subtitle=e["command"])
                check = Gtk.CheckButton(valign=Gtk.Align.CENTER)
                if e["command"] in existing:
                    check.set_active(True)
                    check.set_sensitive(False)
                    row.set_subtitle(f"{e['command']} (already added)")
                row.add_prefix(check)
                row.set_activatable_widget(check)
                listbox.append(row)
                checks.append((check, e))
            scroller = Gtk.ScrolledWindow()
            scroller.set_child(listbox)
            scroller.set_vexpand(True)
            content.append(scroller)

            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, halign=Gtk.Align.END)
            cancel_btn = Gtk.Button(label="Cancel")
            cancel_btn.connect("clicked", lambda _b: dialog.close())
            add_btn = Gtk.Button(label="Add Selected")
            add_btn.add_css_class("suggested-action")
            add_btn.connect("clicked", lambda _b: self.on_import_confirmed(dialog, checks))
            button_box.append(cancel_btn)
            button_box.append(add_btn)
            content.append(button_box)

        toolbar_view.set_content(content)
        dialog.present()

    def on_import_confirmed(self, dialog, checks):
        apps = self.current_session.setdefault("apps", [])
        for check, entry in checks:
            if check.get_active() and check.get_sensitive() and entry["command"] not in apps:
                apps.append(entry["command"])
        config.save(self.data)
        self.refresh_app_list()
        dialog.close()
