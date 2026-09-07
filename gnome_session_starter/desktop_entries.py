"""Shared helpers for turning .desktop Exec= lines into runnable commands."""
import re

# XDG desktop-entry field codes (%f, %U, ...) don't apply to us; strip them.
_FIELD_CODE_RE = re.compile(r"%[fFuUdDnNickvm]")


def clean_exec(exec_value):
    cleaned = _FIELD_CODE_RE.sub("", exec_value)
    return " ".join(cleaned.split())
