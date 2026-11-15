from pathlib import Path
import re
import secrets

from ApplicationAckIntent import installation_sha256
from Records import digest, label, read_record
from RecoveryFence import owner_digest


def rearm_timeout(result):
    records = result.get("records") if isinstance(result, dict) else None
    if isinstance(records, dict) and records.get("application") == "solidworks":
        timeout = records.get("queue_timeout")
        if isinstance(timeout, dict) and timeout.get("version") == 1:
            return timeout
    return None


def rearm_runner_digest(entry):
    return digest({"argv": entry["argv"], "schema": entry["schema"], "pool": entry["pool"],
                   "installation": str(entry["application_installation"])})


def make_rearm_intent(session, runner, adapter, timeout):
    return {
        "version": 1, "job_id": session.spec["id"], "kind": session.spec["kind"], "pool": session.pool,
        "session": session.name, "store": str(adapter.store),
        "generation": session.claim["generation"], "fingerprint": session.claim["fingerprint"],
        "attempt": session.claim["attempt"], "installation_sha256": installation_sha256(runner["application_installation"]),
        "runner_sha256": rearm_runner_digest(runner),
        "original_owner_sha256": owner_digest(adapter.owner), "queue_timeout_sha256": digest(timeout),
        "nonce": secrets.token_hex(32),
    }


def validate_rearm_intent(value):
    if (not isinstance(value, dict) or set(value) != {
        "version", "job_id", "kind", "pool", "session", "store", "generation", "fingerprint", "attempt",
        "installation_sha256", "runner_sha256", "original_owner_sha256", "queue_timeout_sha256", "nonce",
    } or type(value["version"]) is not int or value["version"] != 1
            or not isinstance(value["session"], str) or not re.fullmatch("[0-9a-f]+-[0-9a-f]{8}", value["session"])
            or not isinstance(value["store"], str) or not Path(value["store"]).is_absolute()
            or any(type(value[key]) is not int or value[key] < 1 for key in ("generation", "attempt"))
            or any(not isinstance(value[key], str) or not re.fullmatch("[0-9a-f]{64}", value[key])
                   for key in ("fingerprint", "installation_sha256", "runner_sha256", "original_owner_sha256",
                               "queue_timeout_sha256", "nonce"))):
        raise ValueError("invalid application rearm intent")
    for key in ("job_id", "kind", "pool"):
        label(value[key])
    return value


def read_rearm_intent(path):
    intent = validate_rearm_intent(read_record(path))
    if intent["session"] != path.stem:
        raise ValueError("application rearm intent file does not match its session")
    return intent
