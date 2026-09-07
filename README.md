# GNOME Session Starter

A small GTK4/libadwaita app that replaces "start everything in Startup
Applications" with a picker: it shows a window asking which *session* you
want, then launches the apps configured for that session and exits.

- `Tab` / `Shift+Tab` — move between sessions
- `Enter` — launch the selected session (the default session is pre-selected,
  so `Enter` alone launches it)
- `Escape` — quit without launching anything
- Preferences icon in the header bar — add/remove sessions and edit each
  session's list of commands, and pick which one is the default
- "Import from Startup Applications…" in the session editor — pulls entries
  from `~/.config/autostart/*.desktop` (the same list GNOME's own Startup
  Applications tool manages) so you don't have to retype commands for apps
  you've already got set up there. Things you always want regardless of
  session (an autostart daemon like Atuin, say) can stay in GNOME's Startup
  Applications untouched; everything session-specific goes into a session
  here instead.

## Requirements

- Python 3
- GTK4 + libadwaita GObject introspection bindings (`gir1.2-gtk-4.0`,
  `gir1.2-adw-1` on Debian/Ubuntu)

## Run it

```
./gnome-session-starter            # picker
./gnome-session-starter --prefs    # preferences
```

Config is stored at `~/.config/gnome-session-starter/sessions.json`.

## Install as a Startup Application

Copy (or symlink) `gnome-session-starter.desktop` into
`~/.config/autostart/` so it runs once at login instead of everything in
GNOME's Startup Applications list:

```
mkdir -p ~/.config/autostart
cp gnome-session-starter.desktop ~/.config/autostart/
```

To also get it in your applications menu (for launching it manually, or
opening Preferences), copy both `.desktop` files into
`~/.local/share/applications/`:

```
cp gnome-session-starter.desktop gnome-session-starter-preferences.desktop ~/.local/share/applications/
```

Note the `.desktop` files point at this checkout's path
(`/home/richard/dev/gnome/gnome-session-starter/gnome-session-starter`) — if
you move the checkout, update `Exec=` in both files to match.
