import json
import math
import os
import re
import secrets
import stat
import sys
import time
from pathlib import Path

from Processes import process_start
from Records import bounded, canonical, digest, label, read_record


NAME = "supervisor-capacity.json"
MAX_BYTES = 128 * 1024
HEARTBEAT_SECONDS = 5
FRESH_SECONDS = 20
LIMITING_FACTORS = ("configured", "cpu", "memory", "adaptive")
BLOCKED_STATES = ("paused", "settlement_pending", "pool_full")
DECISION_FIELDS = (
    "active_limit", "calculated_capacity", "reason", "adaptive_reason",
    "adaptive_revision", "upward_blocked_reason", "limiting_factors",
    "memory_estimate_bytes_by_kind", "host_measured_at",
)


def configuration_identity(config, registry_sha256):
    return digest({**config, "state": str(config["state"]),
                   "registry": str(config["registry"]), "registry_sha256": registry_sha256})


def boot_identity():
    if sys.platform == "linux":
        value = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
        if not re.fullmatch(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", value):
            raise ValueError("Linux boot identity is unavailable")
        return value
    return None


def read_snapshot(path):
    if path.is_symlink():
        raise ValueError("capacity snapshot cannot be a symbolic link")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("capacity snapshot must be a private regular file")
        content = source.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("capacity snapshot exceeds its size bound")
    return json.loads(content)


def pause_identity(path):
    try:
        info = (path.parent / "pauses.json").stat()
    except FileNotFoundError:
        return None
    return [info.st_ino, info.st_mtime_ns]


def current_age(stamp, now):
    return type(stamp) in (int, float) and 0 <= now - stamp <= FRESH_SECONDS


class CapacitySnapshot:
    def __init__(self, config, registry_sha256):
        self.path = config["state"] / NAME
        self.owner = None
        self.pools = {}
        self.last_published = None
        self.previous_values = {}
        self.next_write = 0
        self.pause_revision = None
        try:
            pid = os.getpid()
            start = process_start(pid, live=True)
            if start is not None:
                self.owner = {"pid": pid, "start": start, "boot": boot_identity(),
                              "run": secrets.token_hex(16)}
                self.configuration = configuration_identity(config, registry_sha256)
        except (OSError, ValueError):
            self.owner = None

    def begin_pass(self):
        try:
            self.pause_revision = pause_identity(self.path)
        except OSError:
            self.pause_revision = []

    def observe(self, pool, admission, host_sample):
        self.pools[pool] = {
            "state": "evaluated",
            "evaluated": time.monotonic(),
            "host_sample": host_sample,
            "pause_revision": self.pause_revision,
            "decision": {key: admission[key] for key in DECISION_FIELDS},
        }
        self.publish()

    def block(self, pool, reason):
        prior = self.pools.get(pool, {})
        self.pools[pool] = (
            {**prior, "state": "pool_full"} if reason == "pool_full" and prior.get("decision")
            else {"state": reason, "decision": None}
        )

    def publish(self):
        now = time.monotonic()
        if self.owner is None or now < self.next_write:
            return
        values = {
            name: (pool["state"], pool.get("pause_revision"), {
                key: value for key, value in (pool["decision"] or {}).items()
                if key != "host_measured_at"
            })
            for name, pool in self.pools.items()
        }
        if values == self.previous_values and self.last_published is not None and now - self.last_published < HEARTBEAT_SECONDS:
            return
        self.next_write = now + 1
        stage = self.path.with_name(f".{NAME}.pending")
        try:
            stage.unlink(missing_ok=True)
            data = canonical({"capacity_version": 1, "owner": self.owner,
                              "configuration": self.configuration, "published": now,
                              "pools": self.pools}).encode("utf-8")
            if len(data) > MAX_BYTES:
                return
            descriptor = os.open(stage, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                with os.fdopen(descriptor, "wb") as output:
                    output.write(data)
                    output.flush()
                os.replace(stage, self.path)
            finally:
                stage.unlink(missing_ok=True)
        except (OSError, ValueError):
            return
        self.previous_values = values
        self.last_published = now

    def retire(self):
        self.owner = None
        if self.last_published is None:
            return
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            return
        self.last_published = None


def decision_fields(record, settings, kinds):
    if set(record) != set(DECISION_FIELDS):
        raise ValueError("capacity decision fields are invalid")
    bounded(record["active_limit"], 0, bounded(record["calculated_capacity"], 0, settings["max_sessions"]))
    bounded(record["adaptive_revision"], 0, (1 << 63) - 1)
    for key in ("reason", "adaptive_reason", "upward_blocked_reason"):
        text = record[key]
        if text is not None and (not isinstance(text, str) or not 1 <= len(text) <= 128):
            raise ValueError("capacity reason is invalid")
    factors = record["limiting_factors"]
    if not isinstance(factors, list) or not 1 <= len(factors) <= len(LIMITING_FACTORS) or factors != [name for name in LIMITING_FACTORS if name in factors]:
        raise ValueError("capacity limiting factors are invalid")
    estimates = record["memory_estimate_bytes_by_kind"]
    if not isinstance(estimates, dict) or not 1 <= len(estimates) <= 256 or set(estimates) != kinds:
        raise ValueError("capacity estimates do not match the registered kinds")
    for value in estimates.values():
        bounded(value, 1, 1 << 64)
    sample = record["host_measured_at"]
    if type(sample) not in (int, float) or not math.isfinite(sample) or sample <= 0:
        raise ValueError("capacity host time is invalid")


def pool_snapshot(pool, settings, kinds, now, pause_revision):
    state, decision = pool["state"], pool["decision"]
    if state in BLOCKED_STATES and decision is None and set(pool) == {"state", "decision"}:
        return {"state": state, "decision": None}
    if state not in ("evaluated", "pool_full") or set(pool) != {"state", "evaluated", "host_sample", "decision", "pause_revision"}:
        raise ValueError("capacity pool fields are invalid")
    if pool["pause_revision"] != pause_revision:
        return {"state": "unavailable", "decision": None}
    if not current_age(pool["evaluated"], now) or not current_age(pool["host_sample"], now) or pool["host_sample"] > pool["evaluated"]:
        return {"state": "pool_full" if state == "pool_full" else "unavailable", "decision": None}
    decision_fields(decision, settings, kinds)
    return {"state": state, "decision": {**decision, "age_seconds": now - pool["evaluated"]}}


def capacity_status(config):
    path = config["state"] / NAME
    try:
        record = read_snapshot(path)
        owner = record["owner"]
        if (set(record) != {"capacity_version", "owner", "configuration", "published", "pools"}
                or type(record["capacity_version"]) is not int or record["capacity_version"] != 1
                or set(owner) != {"pid", "start", "boot", "run"}):
            return {}
        pid = bounded(owner["pid"], 2, (1 << 32) - 1)
        if not isinstance(owner["start"], str) or not re.fullmatch(r"[0-9a-f]{32}", owner["run"]):
            return {}
        if not current_age(record["published"], time.monotonic()) or owner["boot"] != boot_identity() or process_start(pid, live=True) != owner["start"]:
            return {}
        registry = read_record(config["registry"])
        if record["configuration"] != configuration_identity(config, digest(registry)):
            return {}
        if not isinstance(record["pools"], dict) or not set(record["pools"]) <= config["pools"].keys():
            return {}
        kinds = {name: set() for name in config["pools"]}
        for kind, entry in registry["runners"].items():
            kinds[entry["pool"]].add(label(kind))
        current = read_snapshot(path)
        now = time.monotonic()
        if current["owner"] != owner or current["configuration"] != record["configuration"] or not current_age(record["published"], now):
            return {}
        pause_revision = pause_identity(path)
        return {
            name: pool_snapshot(pool, config["pools"][name], kinds[name], now, pause_revision)
            for name, pool in record["pools"].items()
        }
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError):
        return {}
