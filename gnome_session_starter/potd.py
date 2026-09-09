"""Picture-of-the-day: a cached background image for the picker window.

The picker must appear (and be able to quit) instantly, so it never fetches
over the network itself. Instead it shows whatever image is already cached
from a previous run, then spawns a detached background process to fetch
today's picture so it's ready for next time. Bing's unofficial "image
archive" endpoint is used because it needs no API key and no signup.
"""
import json
import os
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "gnome-session-starter" / "potd"
IMAGE_FILE = CACHE_DIR / "current.jpg"
META_FILE = CACHE_DIR / "current.json"

BING_API_URL = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
REQUEST_TIMEOUT = 15


def cached_image_path():
    """Return the path to the cached image, or None if nothing is cached yet."""
    return IMAGE_FILE if IMAGE_FILE.exists() else None


def _load_meta():
    try:
        with open(META_FILE, "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_meta(meta):
    with open(META_FILE, "w") as f:
        json.dump(meta, f)


def _already_fresh():
    return _load_meta().get("date") == date.today().isoformat()


def request_refresh():
    """Spawn a detached background process to refresh the cached image, if needed.

    Skips spawning entirely when today's image is already cached, so a
    normal launch does no work (and touches no process) beyond a file read.
    """
    if _already_fresh():
        return

    repo_root = Path(__file__).resolve().parent.parent
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(repo_root), env.get("PYTHONPATH", "")]))
    subprocess.Popen(
        [sys.executable, "-m", "gnome_session_starter", "--fetch-potd"],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd=str(repo_root),
    )


def fetch_and_store():
    """Download today's picture of the day and cache it. Run in the background process."""
    try:
        with urllib.request.urlopen(BING_API_URL, timeout=REQUEST_TIMEOUT) as resp:
            info = json.load(resp)
        image = info["images"][0]
        image_url = "https://www.bing.com" + image["url"]
        with urllib.request.urlopen(image_url, timeout=REQUEST_TIMEOUT) as resp:
            image_bytes = resp.read()
    except Exception:
        # Offline, DNS failure, API shape change, etc. Leave the existing
        # cached image (if any) in place and try again on a later launch.
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = IMAGE_FILE.with_suffix(".jpg.tmp")
    with open(tmp, "wb") as f:
        f.write(image_bytes)
    tmp.replace(IMAGE_FILE)

    _save_meta({
        "date": date.today().isoformat(),
        "title": image.get("title", ""),
        "copyright": image.get("copyright", ""),
    })
