"""Preferences window: configure sessions and the apps each one launches."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from . import autostart, config, installed_apps
from .widgets import color_swatch, escape


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

        apps_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        apps_label = Gtk.Label(label="Applications to launch", halign=Gtk.Align.START, hexpand=True)
        apps_label.add_css_class("heading")
        apps_header.append(apps_label)
        add_app_btn = Gtk.Button(label="Add Application")
        add_app_btn.connect("clicked", self.on_add_application_clicked)
        apps_header.append(add_app_btn)
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
            row = Adw.ActionRow(title=escape(s["name"]))
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
            "apps": [dict(a) for a in self.current_session.get("apps", [])],
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
            row.set_title(escape(new_name))

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
            row = Adw.ActionRow(title=escape(app["name"]))
            row.set_title_lines(1)
            row.set_subtitle(escape(app["description"] or app["command"]))
            row.set_subtitle_lines(1)
            row.set_tooltip_text(app["command"])
            if not app["active"]:
                row.add_css_class("dim-label")

            active_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            active_switch.set_tooltip_text("Launch this app with the session")
            active_switch.set_active(app["active"])
            active_switch.connect("state-set", self.on_app_active_toggled, i)
            row.add_prefix(active_switch)

            edit_btn = Gtk.Button(icon_name="document-edit-symbolic", valign=Gtk.Align.CENTER)
            edit_btn.add_css_class("flat")
            edit_btn.set_tooltip_text("Edit")
            edit_btn.connect("clicked", self.on_edit_app, i)
            remove_btn = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
            remove_btn.add_css_class("flat")
            remove_btn.set_tooltip_text("Remove")
            remove_btn.connect("clicked", self.on_remove_app, i)
            row.add_suffix(edit_btn)
            row.add_suffix(remove_btn)
            self.app_listbox.append(row)

    def _add_app(self, app):
        self.current_session.setdefault("apps", []).append(app)
        config.save(self.data)
        self.refresh_app_list()

    def on_remove_app(self, _button, index):
        apps = self.current_session.get("apps", [])
        if 0 <= index < len(apps):
            del apps[index]
            config.save(self.data)
            self.refresh_app_list()

    def on_app_active_toggled(self, _switch, state, index):
        apps = self.current_session.get("apps", [])
        if 0 <= index < len(apps):
            apps[index]["active"] = state
            config.save(self.data)
            row = self.app_listbox.get_row_at_index(index)
            if row is not None:
                if state:
                    row.remove_css_class("dim-label")
                else:
                    row.add_css_class("dim-label")
        return False

    def on_edit_app(self, _button, index):
        apps = self.current_session.get("apps", [])
        if not (0 <= index < len(apps)):
            return
        app = apps[index]

        dialog = Adw.AlertDialog(heading="Edit Application")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        name_row = Adw.EntryRow(title="Name")
        name_row.set_text(app["name"])
        command_row = Adw.EntryRow(title="Command")
        command_row.set_text(app["command"])
        description_row = Adw.EntryRow(title="Description")
        description_row.set_text(app["description"])

        group = Adw.PreferencesGroup()
        group.add(name_row)
        group.add(command_row)
        group.add(description_row)
        box.append(group)
        dialog.set_extra_child(box)

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")
        dialog.set_close_response("cancel")
        dialog.connect(
            "response", self._on_edit_app_response, index, name_row, command_row, description_row
        )
        dialog.present(self)

    def _on_edit_app_response(self, _dialog, response, index, name_row, command_row, description_row):
        if response != "save":
            return
        apps = self.current_session.get("apps", [])
        if not (0 <= index < len(apps)):
            return
        command = command_row.get_text().strip()
        if not command:
            return
        name = name_row.get_text().strip() or command
        apps[index]["name"] = name
        apps[index]["command"] = command
        apps[index]["description"] = description_row.get_text().strip()
        config.save(self.data)
        self.refresh_app_list()

    def on_import_clicked(self, _button):
        if self.current_session is None:
            return
        entries = autostart.list_entries()
        existing = {a["command"] for a in self.current_session.get("apps", [])}

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
                subtitle = e.get("description") or e["command"]
                row = Adw.ActionRow(title=escape(e["name"]), subtitle=escape(subtitle))
                row.set_title_lines(1)
                row.set_subtitle_lines(1)
                check = Gtk.CheckButton(valign=Gtk.Align.CENTER)
                if e["command"] in existing:
                    check.set_active(True)
                    check.set_sensitive(False)
                    row.set_subtitle(escape(f"{subtitle} (already added)"))
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
        self._add_checked_commands(checks)
        dialog.close()

    def _add_checked_commands(self, checks):
        apps = self.current_session.setdefault("apps", [])
        existing = {a["command"] for a in apps}
        for check, entry in checks:
            if check.get_active() and check.get_sensitive() and entry["command"] not in existing:
                apps.append(config.new_app(
                    entry["command"], name=entry.get("name"), description=entry.get("description", "")
                ))
                existing.add(entry["command"])
        config.save(self.data)
        self.refresh_app_list()

    def on_add_application_clicked(self, _button):
        if self.current_session is None:
            return

        dialog = Adw.Window(
            application=self.get_application(),
            transient_for=self,
            modal=True,
            title="Add Application",
        )
        dialog.set_default_size(480, 560)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)
        dialog.set_content(toolbar_view)

        stack = Gtk.Stack()
        switcher = Gtk.StackSwitcher(stack=stack, halign=Gtk.Align.CENTER)
        switcher.set_margin_top(6)
        header.set_title_widget(switcher)

        stack.add_titled(
            self._build_from_list_page(dialog), "list", "From Application List"
        )
        stack.add_titled(
            self._build_manual_entry_page(dialog), "manual", "Manually Enter Details"
        )
        toolbar_view.set_content(stack)

        dialog.present()

    def _build_from_list_page(self, dialog):
        entries = installed_apps.list_installed_apps()
        existing = {a["command"] for a in self.current_session.get("apps", [])}

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)

        search = Gtk.SearchEntry()
        search.set_placeholder_text("Search installed applications…")
        content.append(search)

        listbox = Gtk.ListBox()
        listbox.add_css_class("boxed-list")
        checks = []
        for e in entries:
            subtitle = e.get("description") or e["command"]
            row = Adw.ActionRow(title=escape(e["name"]), subtitle=escape(subtitle))
            row.set_title_lines(1)
            row.set_subtitle_lines(1)
            if e["icon"] is not None:
                row.add_prefix(Gtk.Image.new_from_gicon(e["icon"]))
            check = Gtk.CheckButton(valign=Gtk.Align.CENTER)
            if e["command"] in existing:
                check.set_active(True)
                check.set_sensitive(False)
                row.set_subtitle(escape(f"{subtitle} (already added)"))
            row.add_prefix(check)
            row.set_activatable_widget(check)
            listbox.append(row)
            checks.append((check, e))

        def filter_func(row):
            query = search.get_text().strip().lower()
            if not query:
                return True
            return query in checks[row.get_index()][1]["name"].lower()

        listbox.set_filter_func(filter_func)
        search.connect("search-changed", lambda _e: listbox.invalidate_filter())

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(listbox)
        scroller.set_vexpand(True)
        content.append(scroller)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, halign=Gtk.Align.END)
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _b: dialog.close())
        add_btn = Gtk.Button(label="Add Selected")
        add_btn.add_css_class("suggested-action")

        def confirm(_b):
            self._add_checked_commands(checks)
            dialog.close()

        add_btn.connect("clicked", confirm)
        button_box.append(cancel_btn)
        button_box.append(add_btn)
        content.append(button_box)

        return content

    def _build_manual_entry_page(self, dialog):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)

        name_row = Adw.EntryRow(title="Name")
        command_row = Adw.EntryRow(title="Command")
        description_row = Adw.EntryRow(title="Description")
        group = Adw.PreferencesGroup()
        group.add(name_row)
        group.add(command_row)
        group.add(description_row)
        content.append(group)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, halign=Gtk.Align.END)
        button_box.set_valign(Gtk.Align.END)
        button_box.set_vexpand(True)
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _b: dialog.close())
        add_btn = Gtk.Button(label="Add")
        add_btn.add_css_class("suggested-action")

        def confirm(_b):
            command = command_row.get_text().strip()
            if not command:
                return
            name = name_row.get_text().strip() or command
            description = description_row.get_text().strip()
            self._add_app(config.new_app(command, name=name, description=description))
            dialog.close()

        add_btn.connect("clicked", confirm)
        command_row.connect("entry-activated", confirm)
        button_box.append(cancel_btn)
        button_box.append(add_btn)
        content.append(button_box)

        return content
