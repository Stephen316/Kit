import hashlib
import hmac
import re


class StaleOwner(ValueError):
    pass


def owner_digest(owner):
    if not isinstance(owner, str) or not re.fullmatch("[0-9a-f]{64}", owner):
        raise ValueError("supervisor owner must be 64 lowercase hexadecimal characters")
    return hashlib.sha256(owner.encode("ascii")).hexdigest()


def rotate_owner(ledger, owner):
    digest = owner_digest(owner)
    ledger.db.execute("CREATE TABLE IF NOT EXISTS supervisor_owner (id INTEGER PRIMARY KEY CHECK (id=1), version INTEGER NOT NULL CHECK (version=1), token_hash TEXT NOT NULL)")
    current = ledger.db.execute("SELECT version FROM supervisor_owner WHERE id=1").fetchone()
    if current is not None and current["version"] != 1:
        raise ValueError("unsupported supervisor recovery fence version")
    ledger.db.execute("INSERT INTO supervisor_owner VALUES (1,1,?) ON CONFLICT(id) DO UPDATE SET version=excluded.version,token_hash=excluded.token_hash", (digest,))
    ledger.event(None, "supervisor_owner_rotated", {"recovery_fence_version": 1})
    return {"recovery_fence_version": 1}


def check_owner(ledger, owner):
    if owner is None:
        return
    digest = owner_digest(owner)
    if ledger.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='supervisor_owner'").fetchone() is None:
        raise StaleOwner("supervisor owner has not been installed")
    row = ledger.db.execute("SELECT version,token_hash FROM supervisor_owner WHERE id=1").fetchone()
    if row is None or row["version"] != 1 or not hmac.compare_digest(row["token_hash"], digest):
        raise StaleOwner("supervisor owner was replaced during recovery")
