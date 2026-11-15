import time


DEADLINE_WINDOW_SECONDS = 600


class AdaptiveCapacity:
    def __init__(self, enabled):
        self.enabled = enabled
        self.pools = {}

    def state(self, pool):
        return self.pools.setdefault(pool, {"target": None, "healthy_since": None, "next_increase": None, "deadlines": [], "below_reserve": False, "revision": 0, "reason": "initial"})

    def started(self, pool):
        if not self.enabled:
            return
        state = self.state(pool)
        if state["healthy_since"] is None:
            now = time.monotonic()
            state["healthy_since"] = now
            state["next_increase"] = now + 60

    def backoff(self, state, reason, now):
        before = state["target"]
        state["target"] = max(1, (before or 1) // 2)
        state["healthy_since"] = now if state["healthy_since"] is not None else None
        state["next_increase"] = now + 60 if state["healthy_since"] is not None else None
        state["revision"] += 1
        state["reason"] = reason
        return {"before_limit": before, "target_limit": state["target"], "adaptive_reason": reason, "adaptive_revision": state["revision"]}

    def finished(self, pool, session, outcome, receipt):
        if not self.enabled:
            return None
        state = self.state(pool)
        now = time.monotonic()
        reason = receipt.get("stop_reason")
        if outcome in {"retry", "rejected"} or reason is not None:
            state["healthy_since"] = now
            state["next_increase"] = now + 60
        if reason == "memory_limit":
            return self.backoff(state, "memory_limit", now)
        if reason is None and receipt.get("kernel_oom") is not None:
            return self.backoff(state, "linux_memcg_oom", now)
        if reason != "deadline":
            return None
        state["deadlines"] = [(name, stamp) for name, stamp in state["deadlines"] if now - stamp <= DEADLINE_WINDOW_SECONDS]
        if not state["deadlines"]:
            state["deadlines"].append((session, now))
            return None
        first_session, first_at = state["deadlines"][0]
        if session == first_session:
            return None
        state["deadlines"] = []
        return {
            **self.backoff(state, "deadline_pair", now),
            "deadline_count": 2,
            "deadline_window_seconds": DEADLINE_WINDOW_SECONDS,
            "deadline_sessions": [first_session, session],
            "deadline_elapsed_seconds": now - first_at,
        }

    def limit(self, pool, capacity, host, reserved_memory, estimate):
        if not self.enabled:
            return {"active_limit": capacity, "calculated_capacity": capacity, "adaptive_reason": "disabled", "adaptive_revision": 0, "upward_blocked_reason": "disabled"}
        state = self.state(pool)
        now = time.monotonic()
        state["deadlines"] = [(name, stamp) for name, stamp in state["deadlines"] if now - stamp <= DEADLINE_WINDOW_SECONDS]
        if state["target"] is None and capacity > 0:
            state["target"] = max(1, capacity // 2)
            state["revision"] += 1
        elif capacity > 0 and state["target"] is not None:
            state["target"] = min(state["target"], capacity)
        below = host["available_memory_bytes"] < reserved_memory
        if below and not state["below_reserve"]:
            self.backoff(state, "memory_headroom", now)
        if below and state["healthy_since"] is not None:
            state["healthy_since"] = now
            state["next_increase"] = now + 60
        state["below_reserve"] = below
        blocked = self.upward_block(state, host, reserved_memory, estimate, now)
        if blocked is None and state["target"] is not None and state["target"] < capacity:
            state["target"] += 1
            state["next_increase"] = now + 60
            state["revision"] += 1
            state["reason"] = "healthy_minute"
        healthy = None if state["healthy_since"] is None else now - state["healthy_since"]
        return {"active_limit": min(capacity, state["target"] or 0), "calculated_capacity": capacity, "adaptive_reason": state["reason"], "adaptive_revision": state["revision"], "upward_blocked_reason": blocked, "healthy_seconds": healthy, "pending_deadline_stops": len(state["deadlines"])}

    def upward_block(self, state, host, reserved_memory, estimate, now):
        if state["next_increase"] is None:
            return "no work started"
        if now < state["next_increase"]:
            return "healthy minute incomplete"
        load = host.get("load_average_1m")
        if load is None:
            return "load measurement unavailable"
        if load >= host["logical_cpus"] * 0.85:
            return "load threshold"
        if host["available_memory_bytes"] <= reserved_memory + estimate:
            return "memory threshold"
        if host.get("memory_pressure_required", True):
            pressure = host.get("memory_some_avg10")
            if pressure is None:
                return "memory pressure measurement unavailable"
            if pressure >= 10:
                return "memory pressure threshold"
        return None
