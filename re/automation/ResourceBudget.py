import time

from HostResources import group_memory, host_resources
from MemoryHistory import MemoryHistory


class ResourceBudget:
    def __init__(self, config, registry):
        self.reserved_cpus = config["reserved_cpus"]
        self.reserved_memory = config["reserved_memory_mib"] * 1048576
        self.registry = registry
        self.history = MemoryHistory(config["state"] / "memory-history.json")
        self.history_error = None
        self.host = None
        self.groups = {}
        self.host_groups = {}
        self.measured_at = None
        self.next_host = 0

    def record(self, specification, session, outcome, stale, receipt, report):
        if stale is not False or outcome != "completed" or self.history_error is not None:
            return
        try:
            recorded = self.history.record(specification, session, receipt)
        except (OSError, ValueError) as error:
            self.history_error = f"{type(error).__name__}: {error}"[:2048]
            report("memory_history_error", None, {"error": self.history_error, "learning_disabled_until_restart": True})
            return
        if recorded is not None:
            initial = self.registry.runners[specification["kind"]]["initial_peak_memory_mib"] * 1048576
            report("memory_estimate", None, {"session": session, "job": specification["id"], **recorded, **self.history.estimate(specification["kind"], specification["tool_version"], initial)})

    def refresh(self, running):
        now = time.monotonic()
        self.groups = group_memory({session.pid for session in running.values()})
        if now >= self.next_host:
            self.host = host_resources()
            self.host_groups = dict(self.groups)
            self.measured_at = time.time()
            self.next_host = now + 5

    def admission(self, pool, settings, running):
        entries = [entry for entry in self.registry.runners.values() if entry["pool"] == pool]
        threads = max(entry["threads"] for entry in entries)
        estimate = max(self.history.admission_estimate(kind, entry["initial_peak_memory_mib"] * 1048576) for kind, entry in self.registry.runners.items() if entry["pool"] == pool)
        used_cpus = 0
        pending_memory = 0
        count = 0
        for session in running.values():
            entry = self.registry.runners[session.spec["kind"]]
            used_cpus += entry["threads"]
            estimate_bytes = self.history.estimate(session.spec["kind"], session.spec["tool_version"], entry["initial_peak_memory_mib"] * 1048576)["estimate_bytes"]
            expected_bytes = max(estimate_bytes, self.groups.get(session.pid, estimate_bytes))
            pending_memory += max(0, expected_bytes - self.host_groups.get(session.pid, 0))
            count += session.pool == pool
        cpu_slots = max(0, self.host["logical_cpus"] - self.reserved_cpus - used_cpus) // threads
        memory_slots = max(0, self.host["available_memory_bytes"] - self.reserved_memory - pending_memory) // estimate
        slots = min(settings["max_sessions"] - count, cpu_slots, memory_slots)
        reason = "pool limit" if count >= settings["max_sessions"] else "cpu headroom" if cpu_slots == 0 else "memory headroom" if memory_slots == 0 else None
        return {"additional_sessions": max(0, slots), "running": count, "reason": reason, "threads_per_session": threads, "estimated_memory_bytes": estimate, "host_measured_at": self.measured_at, "host": self.host, "reserved_cpus": self.reserved_cpus, "reserved_memory_bytes": self.reserved_memory}
