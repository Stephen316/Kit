import json as JsonCodec
from typing import Mapping


# a pool may grow only after a full healthy interval with spare resources
def CheckAdaptive(Events: list[Mapping[str, object]]) -> None:
    Admissions = [
        JsonCodec.loads(JsonCodec.dumps(Event))
        for Event in Events
        if Event.get("event") == "admission"
    ]
    First = Admissions[0]
    assert First["active_limit"] == max(1, First["calculated_capacity"] // 2)
    assert all(
        Event["active_limit"] <= Event["calculated_capacity"] for Event in Admissions
    )
    Increased = list(
        {
            Event["adaptive_revision"]: Event
            for Event in reversed(Admissions)
            if Event["adaptive_reason"] == "healthy_minute"
        }.values()
    )
    for Event in Increased:
        assert Event["healthy_seconds"] >= 60
        assert Event["host"]["load_average_1m"] < Event["host"]["logical_cpus"] * 0.85
        assert (
            Event["host"]["available_memory_bytes"]
            > Event["reserved_memory_bytes"] + Event["estimated_memory_bytes"]
        )
        if Event["host"]["memory_pressure_required"]:
            assert Event["host"]["memory_some_avg10"] < 10
    print(
        JsonCodec.dumps(
            {
                "adaptive_upward_branch_verified": bool(Increased),
                "last_admission": Admissions[-1],
            }
        )
    )
