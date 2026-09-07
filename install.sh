#!/usr/bin/env bash
# Install Session Starter's .desktop entries and icon so it shows up in
# GNOME's application list. Symlinks (not copies) so future edits to this
# checkout take effect without reinstalling.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

mkdir -p "$APPS_DIR" "$ICON_DIR"

ln -sf "$SCRIPT_DIR/io.github.artumi_richard.GnomeSessionStarter.desktop" \
    "$APPS_DIR/io.github.artumi_richard.GnomeSessionStarter.desktop"
ln -sf "$SCRIPT_DIR/io.github.artumi_richard.GnomeSessionStarter.Preferences.desktop" \
    "$APPS_DIR/io.github.artumi_richard.GnomeSessionStarter.Preferences.desktop"
ln -sf "$SCRIPT_DIR/data/icons/io.github.artumi_richard.GnomeSessionStarter.svg" \
    "$ICON_DIR/io.github.artumi_richard.GnomeSessionStarter.svg"

update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
gtk-update-icon-cache -q "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" >/dev/null 2>&1 || true

echo "Installed. \"Session Starter\" and \"Session Starter Preferences\" should now appear in the application list."
echo "To also run it on login instead of via GNOME's own Startup Applications entries, add it there too - see README.md."
