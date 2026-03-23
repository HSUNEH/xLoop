#!/usr/bin/env python3
"""I/O utilities — atomic JSON writes, advisory file locks, .bak backup/recovery."""

import json
import os
import sys
import tempfile
from pathlib import Path

# ── fcntl availability ──────────────────────────────────────────────

try:
    import fcntl
    _has_fcntl = True
except ImportError:
    _has_fcntl = False


# ── Atomic write ────────────────────────────────────────────────────

def _atomic_write_json(path, data):
    """Write JSON to *path* atomically via tempfile + os.replace().

    Ensures that a crash mid-write never leaves a truncated file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, str(path))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── Advisory file lock ──────────────────────────────────────────────

class _locked_file:
    """Context manager for advisory file locking.

    Uses fcntl.flock on macOS/Linux.  Falls back to a no-op (with a
    warning on stderr) when fcntl is unavailable (e.g. Windows).
    """

    def __init__(self, path):
        self._lock_path = Path(path).with_suffix(".lock")
        self._lock_fd = None

    def __enter__(self):
        if _has_fcntl:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            self._lock_fd = open(self._lock_path, "w")
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX)
        else:
            print(
                "[WARNING] fcntl not available — skipping advisory lock",
                file=sys.stderr,
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._lock_fd is not None:
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
            self._lock_fd.close()
            self._lock_fd = None
        return False


def locked_write_json(path, data):
    """Acquire an advisory lock, then atomically write JSON."""
    with _locked_file(path):
        _atomic_write_json(path, data)


# ── .bak backup / recovery ─────────────────────────────────────────

_MAX_BACKUPS = 3


def _rotate_backups(path):
    """Keep at most _MAX_BACKUPS .bak files for *path*.

    Files are named  path.bak.1  (newest) through  path.bak.N  (oldest).
    """
    path = Path(path)
    # Shift existing backups: .bak.2 -> .bak.3, .bak.1 -> .bak.2 …
    for i in range(_MAX_BACKUPS, 1, -1):
        older = path.with_suffix(f".bak.{i}")
        newer = path.with_suffix(f".bak.{i - 1}")
        if newer.exists():
            if i == _MAX_BACKUPS and older.exists():
                older.unlink()
            if newer.exists():
                newer.rename(older)
    # Current file → .bak.1
    bak1 = path.with_suffix(".bak.1")
    if path.exists():
        try:
            import shutil
            shutil.copy2(str(path), str(bak1))
        except OSError:
            pass


def save_json_with_backup(path, data):
    """Rotate .bak files, then atomically write *data* to *path*."""
    _rotate_backups(path)
    _atomic_write_json(path, data)


def load_json_with_recovery(path):
    """Load JSON from *path*, falling back to .bak files on corruption.

    Returns the parsed dict.  Raises FileNotFoundError when neither the
    main file nor any backup exists.
    """
    path = Path(path)
    # Try main file first
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(
                f"[WARNING] Corrupted JSON: {path} — trying backups",
                file=sys.stderr,
            )

    # Try backups from newest to oldest
    for i in range(1, _MAX_BACKUPS + 1):
        bak = path.with_suffix(f".bak.{i}")
        if bak.exists():
            try:
                data = json.loads(bak.read_text(encoding="utf-8"))
                # Restore good backup to main file
                _atomic_write_json(path, data)
                print(
                    f"[RECOVERED] Restored {path} from {bak.name}",
                    file=sys.stderr,
                )
                return data
            except json.JSONDecodeError:
                continue

    raise FileNotFoundError(f"No valid JSON file or backup found: {path}")


# ── Structured error helpers ────────────────────────────────────────

# Error code ranges:
#   E1xx — state management (session, pipeline, handoff)
#   E2xx — search / research
#   E3xx — execution engine
#   E4xx — evaluation engine
#   E5xx — drift / routing

def _now_iso():
    from datetime import datetime
    return datetime.now().replace(microsecond=0).isoformat()


def make_error(code, message, phase=None, recoverable=False, context=None):
    """Create a structured error dictionary.

    Args:
        code: error code string, e.g. "E101"
        message: human-readable description
        phase: pipeline phase number or name (optional)
        recoverable: whether the caller can retry
        context: extra context dict (optional)
    """
    return {
        "error_code": code,
        "message": message,
        "phase": phase,
        "recoverable": recoverable,
        "context": context or {},
        "timestamp": _now_iso(),
    }


def _handle_error(err_dict, log_path=None):
    """Handle a structured error: print to stderr AND append to JSONL log.

    Args:
        err_dict: dict from make_error()
        log_path: optional Path for progress.jsonl; if None, stderr only
    """
    # Always print to stderr (backward compatible)
    code = err_dict.get("error_code", "E000")
    msg = err_dict.get("message", "Unknown error")
    phase = err_dict.get("phase")
    prefix = f"[{code}]"
    if phase is not None:
        prefix += f" [Phase {phase}]"
    print(f"{prefix} {msg}", file=sys.stderr)

    # Append to JSONL log if path provided
    if log_path is not None:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": err_dict.get("timestamp", _now_iso()),
            "level": "error",
            "error_code": code,
            "phase": phase,
            "msg": msg,
            "recoverable": err_dict.get("recoverable", False),
            "context": err_dict.get("context", {}),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
