import re
import signal


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def verified_oom(observation, receipt):
    if (observation is None or receipt["orphan"] is not False
            or receipt["stop_reason"] is not None or receipt["signal"] != signal.SIGKILL):
        return None
    group = observation["group"]
    worker = observation["worker"]
    before, after = (observation[key] for key in ("before", "after"))
    pid = receipt["pid"]
    require(
        isinstance(group, str) and re.fullmatch(r"/kit-a08b-oom-[0-9a-f]{16}", group)
        and observation["case"] == "memory_cap"
        and type(worker["proc_start_ticks"]) is int and worker["proc_start_ticks"] > 0
        and type(worker["uid"]) is int and worker["uid"] > 0
        and type(worker["pid"]) is int and worker["pid"] == pid
        and f"linux:{worker['proc_start_ticks']}" == receipt["process_start"]
        and receipt["exit_status"] is None and observation["termination"] == -signal.SIGKILL,
        "kernel OOM worker identity differs from the reaped session",
    )
    require(
        before["members"] == [str(pid)] and after["members"] == []
        and all(type(before[key]) is int and type(after[key]) is int
                and before[key] > 0 and after[key] == before[key] for key in ("device", "inode")),
        "kernel OOM observer did not verify the same private singleton cgroup",
    )
    old, new = (row["memory_events_local"] for row in (before, after))
    required = {"max", "oom", "oom_kill"}
    require(
        old.keys() == new.keys() and required <= old.keys()
        and all(type(old[key]) is int and type(new[key]) is int and 0 <= old[key] <= new[key] for key in old),
        "kernel OOM local counters changed schema or reset",
    )
    deltas = {key: new[key] - old[key] for key in required}
    require(
        deltas["max"] > 0 and deltas["oom"] > 0 and deltas["oom_kill"] == 1
        and new.get("oom_group_kill", 0) == old.get("oom_group_kill", 0),
        "kernel OOM observer did not identify one local victim",
    )
    messages = observation["kernel_messages"]
    require(isinstance(messages, list) and len(messages) == 1, "expected one matching kernel OOM record")
    record = messages[0]
    require(
        type(record["priority"]) is int and 0 <= record["priority"] < 8
        and type(record["sequence"]) is int and record["sequence"] >= 0
        and type(record["boot_microseconds"]) is int and record["boot_microseconds"] > 0
        and record["constraint"] == "CONSTRAINT_MEMCG"
        and type(record["pid"]) is int and type(record["uid"]) is int
        and record["pid"] == pid and record["uid"] == worker["uid"]
        and record["oom_memcg"] == record["task_memcg"] == group,
        "kernel record does not identify the owned Linux memory-cgroup victim",
    )
    return {
        "evidence_version": 1,
        "kind": "linux_memcg_oom",
        "group": group,
        "device": before["device"],
        "inode": before["inode"],
        "local_delta": deltas,
        "kernel_record": {key: record[key] for key in (
            "priority", "sequence", "boot_microseconds", "constraint", "pid", "uid",
            "oom_memcg", "task_memcg",
        )},
    }
