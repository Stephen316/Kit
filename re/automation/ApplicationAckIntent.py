import hashlib
import os
import re
import secrets
import stat
import subprocess
import time
from pathlib import Path

from Records import label, read_record
from RecoveryFence import StaleOwner


def installation_sha256(path):
    attributes = path.lstat()
    if (not stat.S_ISREG(attributes.st_mode) or attributes.st_nlink != 1
            or getattr(attributes, "st_file_attributes", 0) & 0x400):
        raise ValueError("application installation must be a regular file without links")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as source:
        opened = os.fstat(source.fileno())
        if (attributes.st_dev, attributes.st_ino, attributes.st_mode) != (opened.st_dev, opened.st_ino, opened.st_mode):
            raise ValueError("application installation changed during settlement")
        content = source.read(1024 * 1024 + 1)
    if len(content) > 1024 * 1024:
        raise ValueError("application installation exceeds its record limit")
    return hashlib.sha256(content).hexdigest()


def make_intent(session, installation, store):
    return {
        "version": 1, "session": session.name, "job": session.spec["id"],
        "kind": session.spec["kind"], "pool": session.pool, "store": str(store),
        "generation": session.claim["generation"], "fingerprint": session.claim["fingerprint"],
        "attempts": session.claim["attempt"], "installation_sha256": installation_sha256(installation),
        "nonce": secrets.token_hex(32),
    }


def read_intent(path):
    intent = read_record(path)
    if (set(intent) != {"version", "session", "job", "kind", "pool", "store", "generation",
                       "fingerprint", "attempts", "installation_sha256", "nonce"}
            or type(intent["version"]) is not int or intent["version"] != 1
            or intent["session"] != path.stem or not re.fullmatch("[0-9a-f]+-[0-9a-f]{8}", path.stem)
            or not isinstance(intent["store"], str) or not Path(intent["store"]).is_absolute()
            or any(type(intent[key]) is not int or intent[key] <= 0 for key in ("generation", "attempts"))
            or any(not isinstance(intent[key], str) or not re.fullmatch("[0-9a-f]{64}", intent[key])
                   for key in ("fingerprint", "installation_sha256", "nonce"))):
        raise ValueError("invalid application acknowledgement intent")
    for key in ("job", "kind", "pool"):
        label(intent[key])
    return intent


def current_completion(adapter, intent):
    try:
        status = adapter.ReadStatus(intent["job"])
    except StaleOwner:
        raise
    except (OSError, subprocess.SubprocessError, ValueError):
        time.sleep(0.25)
        status = adapter.ReadStatus(intent["job"])
    rows = status["jobs"]
    return len(rows) == 1 and rows[0]["state"] == "completed" and all(
        rows[0][key] == intent[key] for key in ("kind", "generation", "fingerprint", "attempts")
    )
