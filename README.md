# GNOME Session Starter

A small GTK4/libadwaita app that replaces "start everything in Startup
Applications" with a picker: it shows a window asking which *session* you
want, then launches the apps configured for that session and exits.

- `Tab` / `Shift+Tab` — move between sessions
- `Enter` — launch the selected session (the default session is pre-selected,
  so `Enter` alone launches it)
- `Escape` — quit without launching anything
- Preferences icon in the header bar — add, duplicate, or delete sessions
  (deleting asks for confirmation first), edit each session's list of
  apps, pick which one is the default, and set a color for it
- Each session gets a color swatch, shown next to it in both the picker and
  Preferences, so you can tell sessions apart at a glance
- Each app in a session has a name, a description, and a command, plus a
  switch to mark it inactive — an inactive app stays in the list (so you
  don't lose the command) but is skipped when the session launches. Every
  app row has edit (rename/change command/description), reorder, and
  remove buttons.
- "Import from Startup Applications…" in the session editor — pulls entries
  from `~/.config/autostart/*.desktop` (the same list GNOME's own Startup
  Applications tool manages) so you don't have to retype commands for apps
  you've already got set up there. Things you always want regardless of
  session (an autostart daemon like Atuin, say) can stay in GNOME's Startup
  Applications untouched; everything session-specific goes into a session
  here instead.
- "Add Installed Application…" in the session editor — a searchable list of
  everything GNOME's own app grid would show (from `Gio.AppInfo`, so it
  covers system, Flatpak, and Snap apps too), with the exact command each
  one actually launches. This is the fix for something like a Steam game
  (e.g. Dwarf Fortress) that shows up in the app grid but has no matching
  binary on `$PATH` — its real launch command turns out to be something
  like `steam steam://rungameid/975370`, which this list surfaces for you
  instead of you having to go hunting for it.
- Both importers carry across each app's description too (the `Comment=`
  field from its `.desktop` entry), so you don't have to write your own.

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

### Launching something that isn't a plain app

The "Command to launch" field (and each imported/added entry) is just a
shell command run directly — it doesn't have to be a bare app name. For
something like opening a terminal running an editor, e.g. neovim inside
kitty, type the terminal's `-e`/exec flag and the program as one command:

```
kitty -e nvim
kitty -e nvim ~/some/project
```

Each session app is launched independently (not through a shell), so
pipes/`&&`/env vars written directly in the field won't work — but a
single command with arguments like the above does.

## Install as a Startup Application

This app is meant to *replace* Startup Applications for everything that's
session-specific — but it still needs to be launched by Startup Applications
itself, alongside anything you genuinely want running on every login
regardless of session (a background daemon like Atuin, say). So the setup
is:

1. Add **Session Starter** itself as an entry in GNOME's Startup
   Applications tool (search "Startup Applications" in Activities, or run
   `gnome-session-properties`), pointing at this checkout's
   `gnome-session-starter` script.
2. Leave any always-needed apps (Atuin, etc.) as their own separate entries
   there too.
3. Move everything else — the apps that differ per session — out of Startup
   Applications and into a session here (use "Import from Startup
   Applications…" in the session editor to pull them across without
   retyping commands).

You can add the entry through the Startup Applications GUI directly (Add →
browse to `gnome-session-starter.desktop`), or install the `.desktop` file
for it to pick up:

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
