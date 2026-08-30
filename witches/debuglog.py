"""Diagnostic log.

The packaged .app has no console, so anything worth debugging has to land in a
file. Set CAULDRON_LOG=0 to turn this off.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

ENABLED = os.environ.get("CAULDRON_LOG", "1").lower() not in ("0", "", "off", "false")

_handle = None
_path = None


def log_path():
    """Where the log lives. Prefers the macOS Logs folder, else a temp dir."""
    global _path
    if _path is None:
        base = Path.home() / "Library" / "Logs"
        if not base.is_dir():
            base = Path(tempfile.gettempdir())
        _path = base / "CauldronCompany.log"
    return _path


def _stream():
    global _handle
    if _handle is None:
        try:
            _handle = log_path().open("a", buffering=1)
        except OSError:
            return None
    return _handle


def log(msg):
    """Append one line. Never raises: a broken log must not break the game."""
    if not ENABLED:
        return
    stream = _stream()
    if stream is None:
        return
    try:
        stream.write(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}  {msg}\n")
    except (OSError, ValueError):
        pass


def banner(msg):
    log("")
    log(f"===== {msg} =====")
