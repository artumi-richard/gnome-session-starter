"""Launching commands for a session."""
import shlex
import subprocess


def launch_session(session):
    for app in session.get("apps", []):
        cmd = app if isinstance(app, str) else app.get("command", "")
        cmd = cmd.strip()
        if not cmd:
            continue
        try:
            subprocess.Popen(
                shlex.split(cmd),
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (FileNotFoundError, ValueError):
            # Fall back to a shell in case it's a shell one-liner (pipes, env vars, etc.)
            subprocess.Popen(
                cmd,
                shell=True,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
