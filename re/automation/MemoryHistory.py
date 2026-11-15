import re
from pathlib import Path

from Records import bounded, label, read_record
from Sessions import write_private


MAX_MEMORY_BYTES = (1 << 63) - 1
MIN_INITIAL_BYTES = 1 << 20
MAX_OOM_SESSIONS = MAX_MEMORY_BYTES.bit_length() - MIN_INITIAL_BYTES.bit_length() + 1


def checked_session(session):
    if not isinstance(session, str) or not re.fullmatch(r"[a-f0-9]{1,32}-[a-f0-9]{1,16}", session):
        raise ValueError("memory history requires a physical session identity")
    return session


class MemoryHistory:
    def __init__(self, path):
        self.path = Path(path)
        self.records = []
        if self.path.is_symlink():
            raise ValueError("memory history cannot be a symbolic link")
        if not self.path.exists():
            return
        record = read_record(self.path)
        if set(record) != {"history_version", "records"} or type(record["history_version"]) is not int or record["history_version"] not in (1, 2):
            raise ValueError("unsupported memory history version or fields")
        version = record["history_version"]
        if not isinstance(record["records"], list) or len(record["records"]) > 128:
            raise ValueError("memory history must contain at most 128 version records")
        identities = set()
        for entry in record["records"]:
            fields = {"kind", "tool_version", "samples"}
            allowed = (fields, fields | {"oom"}) if version == 2 else (fields,)
            if not isinstance(entry, dict) or set(entry) not in allowed:
                raise ValueError("memory version record fields do not match history version")
            identity = (label(entry["kind"]), label(entry["tool_version"]))
            if identity in identities:
                raise ValueError("memory history repeats a version")
            identities.add(identity)
            sessions = set()
            if "oom" in entry:
                oom = entry["oom"]
                if not isinstance(oom, dict) or set(oom) != {"minimum_bytes", "sessions"}:
                    raise ValueError("OOM floor fields do not match memory history version 2")
                if not isinstance(oom["sessions"], list) or not 1 <= len(oom["sessions"]) <= MAX_OOM_SESSIONS:
                    raise ValueError("OOM floor session count is outside its doubling bound")
                minimum = min(MIN_INITIAL_BYTES << len(oom["sessions"]), MAX_MEMORY_BYTES)
                bounded(oom["minimum_bytes"], minimum, MAX_MEMORY_BYTES)
                sessions = {checked_session(session) for session in oom["sessions"]}
                if len(sessions) != len(oom["sessions"]):
                    raise ValueError("OOM floor repeats a physical session")
            minimum_samples = 0 if "oom" in entry else 1
            if not isinstance(entry["samples"], list) or not minimum_samples <= len(entry["samples"]) <= 50:
                raise ValueError("memory version sample count is outside its bound")
            for sample in entry["samples"]:
                if not isinstance(sample, dict) or set(sample) != {"session", "peak_memory_bytes"}:
                    raise ValueError("memory sample fields do not match version 1")
                session = checked_session(sample["session"])
                if session in sessions:
                    raise ValueError("memory sample must have a unique session identity")
                sessions.add(session)
                bounded(sample["peak_memory_bytes"], 1, MAX_MEMORY_BYTES)
            self.records.append(entry)

    def entry(self, kind, version):
        return next((item for item in self.records if item["kind"] == kind and item["tool_version"] == version), {"kind": kind, "tool_version": version, "samples": []})

    def estimate(self, kind, version, initial):
        entry = self.entry(kind, version)
        samples = entry["samples"]
        estimate, source = initial, "initial"
        if len(samples) >= 5:
            values = sorted(sample["peak_memory_bytes"] for sample in samples)
            percentile = values[(len(values) * 95 + 99) // 100 - 1]
            estimate, source = (percentile * 5 + 3) // 4, "p95+25%"
        floor = entry.get("oom", {}).get("minimum_bytes", 0)
        if floor > estimate:
            estimate, source = floor, "linux_memcg_oom"
        return {"estimate_bytes": estimate, "samples": len(samples), "source": source}

    def admission_estimate(self, kind, initial):
        return max([initial, *(self.estimate(kind, entry["tool_version"], initial)["estimate_bytes"] for entry in self.records if entry["kind"] == kind)])

    def record(self, specification, session, receipt):
        peak = receipt.get("sampled_group_peak_memory_bytes")
        if type(peak) is not int or peak <= 0:
            return None
        bounded(peak, 1, MAX_MEMORY_BYTES)
        kind, version = specification["kind"], specification["tool_version"]
        entry = self.entry(kind, version)
        if session in entry.get("oom", {}).get("sessions", ()) or any(sample["session"] == session for sample in entry["samples"]):
            return None
        updated = {**entry, "samples": [*entry["samples"], {"session": session, "peak_memory_bytes": peak}][-50:]}
        self.save(entry, updated)
        return {"kind": kind, "tool_version": version}

    def record_oom(self, specification, session, initial):
        kind, version = specification["kind"], specification["tool_version"]
        entry = self.entry(kind, version)
        sessions = entry.get("oom", {}).get("sessions", [])
        if checked_session(session) in sessions or any(sample["session"] == session for sample in entry["samples"]):
            return None
        bounded(initial, MIN_INITIAL_BYTES, MAX_MEMORY_BYTES)
        previous = max(initial, self.estimate(kind, version, initial)["estimate_bytes"])
        floor = min(previous * 2, MAX_MEMORY_BYTES)
        if floor <= previous:
            return None
        bounded(len(sessions) + 1, 1, MAX_OOM_SESSIONS)
        self.save(entry, {**entry, "oom": {"minimum_bytes": floor, "sessions": [*sessions, session]}})
        return {"kind": kind, "tool_version": version, "previous_estimate_bytes": previous}

    def save(self, entry, updated):
        records = [*filter(lambda item: item is not entry, self.records), updated][-128:]
        version = 2 if any("oom" in item for item in records) else 1
        write_private(self.path, {"history_version": version, "records": records})
        self.records = records
