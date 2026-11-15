import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.Windows.WaitForExit import WaitForExit


# each sweep step must independently tie physical observations and process cleanup to the immutable workload
def VerifyCalTrial(TrialPath: FilePath, InputHash: str) -> None:
    Trial = JsonCodec.loads((TrialPath / "Trial.json").read_text(encoding="utf-8"))
    Cleanup = JsonCodec.loads((TrialPath / "Cleanup.json").read_text(encoding="utf-8"))
    Launcher = JsonCodec.loads(
        (TrialPath / "SupervisorProcess.json").read_text(encoding="utf-8")
    )
    Interpreter = JsonCodec.loads(
        (TrialPath / "SupervisorInterpreter.json").read_text(encoding="utf-8")
    )
    assert (
        Interpreter["pid"] == Launcher["pid"]
        or Interpreter["parent_pid"] == Launcher["pid"]
    )
    assert Cleanup["job_object"] == Launcher["job_object"]
    assert Cleanup["job_members_empty"] is True and not Cleanup["forced_groups"]
    assert Cleanup["claims_empty"] is True and Cleanup["sessions_empty"] is True
    assert Trial["execution_completed"] is True and Trial["completed_jobs"] == 8
    assert Trial["observed_peak_decode_concurrency"] <= 1
    assert (
        Trial["cpu_measurements_complete"] is True
        and Trial["rss_measurements_complete"] is True
    )
    assert Trial["physical_process_cpu_seconds_observed"] > 0
    assert Trial["peak_worker_or_group_rss_bytes"] > 0
    Observations = Trial["observations"]
    assert (
        Observations["active_group_rss_source"] == "windows:nested_job:WorkingSetSize"
    )
    assert Observations["active_group_samples"] > 0
    assert any(
        Sample["active_group_rss_bytes"] == 0 for Sample in Observations["retained"]
    )
    for Entry in Trial["jobs"]:
        Measurement = Entry["measurement"]
        assert Measurement["worker_peak_working_set_bytes"] > 0
        assert Measurement["input_sha256"] == InputHash
    WaitForExit(Launcher["pid"])
    WaitForExit(Interpreter["pid"])
