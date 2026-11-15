import re
from pathlib import Path

from Records import bounded, label, read_record
from Sessions import write_private


class MemoryHistory:
    def __init__(self, path):
        self.path = Path(path)
        self.records = []
        if self.path.is_symlink():
            raise ValueError("memory history cannot be a symbolic link")
        if not self.path.exists():
            return
        record = read_record(self.path)
        if set(record) != {"history_version", "records"} or type(record["history_version"]) is not int or record["history_version"] != 1:
            raise ValueError("memory history fields do not match version 1")
        if not isinstance(record["records"], list) or len(record["records"]) > 128:
            raise ValueError("memory history must contain at most 128 version records")
        identities = set()
        for entry in record["records"]:
            if not isinstance(entry, dict) or set(entry) != {"kind", "tool_version", "samples"}:
                raise ValueError("memory version record fields do not match version 1")
            identity = (label(entry["kind"]), label(entry["tool_version"]))
            if identity in identities:
                raise ValueError("memory history repeats a version")
            identities.add(identity)
            if not isinstance(entry["samples"], list) or not 1 <= len(entry["samples"]) <= 50:
                raise ValueError("memory version needs between 1 and 50 samples")
            sessions = set()
            for sample in entry["samples"]:
                if not isinstance(sample, dict) or set(sample) != {"session", "peak_memory_bytes"}:
                    raise ValueError("memory sample fields do not match version 1")
                session = sample["session"]
                if not isinstance(session, str) or not re.fullmatch(r"[a-f0-9]{1,32}-[a-f0-9]{1,16}", session) or session in sessions:
                    raise ValueError("memory sample must have a unique session identity")
                sessions.add(session)
                bounded(sample["peak_memory_bytes"], 1, 9223372036854775807)
            self.records.append(entry)

    def estimate(self, kind, version, initial):
        entry = next((item for item in self.records if item["kind"] == kind and item["tool_version"] == version), None)
        if entry is None or len(entry["samples"]) < 5:
            return {"estimate_bytes": initial, "samples": 0 if entry is None else len(entry["samples"]), "source": "initial"}
        values = sorted(sample["peak_memory_bytes"] for sample in entry["samples"])
        percentile = values[(len(values) * 95 + 99) // 100 - 1]
        return {"estimate_bytes": (percentile * 5 + 3) // 4, "samples": len(values), "source": "p95+25%"}

    def admission_estimate(self, kind, initial):
        return max([initial, *(self.estimate(kind, entry["tool_version"], initial)["estimate_bytes"] for entry in self.records if entry["kind"] == kind)])

    def record(self, specification, session, receipt):
        peak = receipt.get("sampled_group_peak_memory_bytes")
        if type(peak) is not int or peak <= 0:
            return None
        bounded(peak, 1, 9223372036854775807)
        kind, version = specification["kind"], specification["tool_version"]
        entry = next((item for item in self.records if item["kind"] == kind and item["tool_version"] == version), None)
        if entry is not None and any(sample["session"] == session for sample in entry["samples"]):
            return None
        samples = [] if entry is None else entry["samples"]
        updated = {"kind": kind, "tool_version": version, "samples": [*samples, {"session": session, "peak_memory_bytes": peak}][-50:]}
        records = [*filter(lambda item: item is not entry, self.records), updated][-128:]
        write_private(self.path, {"history_version": 1, "records": records})
        self.records = records
        return {"kind": kind, "tool_version": version}
