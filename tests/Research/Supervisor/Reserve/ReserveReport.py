import json as JsonCodec

from tests.Research.Supervisor.Reserve.ReserveMemory import KMemoryMib


# real kernel observations must explain the same policy change seen in status and its recovery
def VerifyReserve(
    Output: str, ReserveMib: int, Revision: int, Allocation: dict[str, int]
) -> None:
    Events = [JsonCodec.loads(LineText) for LineText in Output.splitlines()]
    Admissions = [Event for Event in Events if Event.get("event") == "admission"]
    Reserve = ReserveMib * KMemoryMib
    First = Admissions[0]
    assert First["calculated_capacity"] == 4 and First["active_limit"] == 2
    assert First["host"]["available_memory_bytes"] > Reserve
    Reduced = [
        Event
        for Event in Admissions
        if Event["host"]["available_memory_bytes"] < Reserve
    ]
    assert Reduced and {Event["adaptive_revision"] for Event in Reduced} == {Revision}
    Crossing = Reduced[0]
    assert Crossing["reserved_memory_bytes"] == Reserve
    assert Crossing["host"]["memory_source"] == "linux:MemAvailable"
    assert Crossing["adaptive_reason"] == "memory_headroom"
    assert Crossing["running"] == Crossing["calculated_capacity"] == 2
    assert Crossing["active_limit"] == 1
    Recovered = next(
        Event
        for Event in Admissions
        if Event["host_measured_at"] > Crossing["host_measured_at"]
        and Event["running"] == 2
        and Event["calculated_capacity"] == 4
    )
    assert Recovered["host"]["available_memory_bytes"] > Reserve
    assert Recovered["active_limit"] == 1 and Recovered["adaptive_revision"] == Revision
    assert not [Event for Event in Events if Event["event"] == "adaptive_backoff"]
    print(
        JsonCodec.dumps(
            {
                "ambient_reserve_crossing": [First, Crossing, Recovered],
                "owned_allocation": Allocation,
            },
            sort_keys=True,
        )
    )
