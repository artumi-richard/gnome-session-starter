# Session Manager

A small GTK4/libadwaita app that replaces "start everything in Startup
Applications" with a picker: it shows a window asking which *session* you
want, then launches the apps configured for that session and exits.

- `Tab` / `Shift+Tab` — move between sessions
- `Enter` — launch the selected session (the default session is pre-selected,
  so `Enter` alone launches it)
- `Escape` — quit without launching anything
- Preferences icon in the header bar — add/remove sessions and edit each
  session's list of commands, and pick which one is the default

## Requirements

- Python 3
- GTK4 + libadwaita GObject introspection bindings (`gir1.2-gtk-4.0`,
  `gir1.2-adw-1` on Debian/Ubuntu)

## Run it

```
./session-manager            # picker
./session-manager --prefs    # preferences
```

Config is stored at `~/.config/session-manager/sessions.json`.

## Install as a Startup Application

Copy (or symlink) `session-manager.desktop` into
`~/.config/autostart/` so it runs once at login instead of everything in
GNOME's Startup Applications list:

```
mkdir -p ~/.config/autostart
cp session-manager.desktop ~/.config/autostart/
```

To also get it in your applications menu (for launching it manually, or
opening Preferences), copy both `.desktop` files into
`~/.local/share/applications/`:

```
cp session-manager.desktop session-manager-preferences.desktop ~/.local/share/applications/
```
