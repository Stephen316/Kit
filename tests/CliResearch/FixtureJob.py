# lease and pool scenarios need bounded real jobs with deterministic retry behavior
def FixtureJob(JobName: str, *, HoldFirst: bool = False) -> dict[str, object]:
    return {
        "id": JobName,
        "kind": "fixture.decode",
        "inputs": {},
        "options": {"mode": "sleep-first" if HoldFirst else "complete"},
        "rule_version": "rule@1",
        "tool_version": "tool@1",
        "max_attempts": 2,
        "lease_seconds": 3,
        "timeout_seconds": 60,
        "retry_base_seconds": 1,
    }
