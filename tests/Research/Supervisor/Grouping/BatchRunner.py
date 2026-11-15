import hashlib as HashCodec
import json as JsonCodec
import os as OsLayer
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


# distinct member artifacts expose mixed results and deliberate digest failures during group intake
def WriteMember(MemberRoot: FilePath) -> None:
    JobRecord = JsonCodec.loads((MemberRoot / "job.json").read_text(encoding="utf-8"))
    JobSpec = JobRecord["job"]
    OutputBytes = JobSpec["id"].encode("ascii")
    _ = (MemberRoot / "work" / "answer.bin").write_bytes(OutputBytes)
    DigestValue = (
        "0" * 64
        if JobSpec["options"].get("bad_output")
        else HashCodec.sha256(OutputBytes).hexdigest()
    )
    ResultInfo: dict[str, object] = {
        "outcome": "completed",
        "reason": "synthetic grouped reader finished",
        "records": {
            "count": len(JobRecord["inputs"]),
            "inputs": sorted(JobRecord["inputs"]),
            "tokenless": "lease_token" not in JsonCodec.dumps(JobRecord),
        },
        "artifacts": {
            "answer": {
                "path": "answer.bin",
                "sha256": DigestValue,
                "size_bytes": int(JobSpec["options"].get("output_size_mib", 0))
                * 1048576
                or len(OutputBytes),
            }
        },
    }
    _ = (MemberRoot / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )


# one worker must exercise both grouped dispatch and the isolated retry path
def RunBatch(SessionRoot: FilePath) -> None:
    GroupFile = SessionRoot / "group.json"
    GroupInfo = (
        JsonCodec.loads(GroupFile.read_text(encoding="utf-8"))
        if GroupFile.is_file()
        else None
    )
    MemberRoots = (
        [SessionRoot / FilePath(NameText).parent for NameText in GroupInfo["members"]]
        if GroupInfo
        else [SessionRoot]
    )
    JobRecords = [
        JsonCodec.loads((MemberRoot / "job.json").read_text(encoding="utf-8"))
        for MemberRoot in MemberRoots
    ]
    if GroupInfo:
        assert GroupInfo["group_session_version"] == 1
        assert "lease_token" not in JsonCodec.dumps(GroupInfo)
        if any(JobInfo["job"]["options"].get("crash_group") for JobInfo in JobRecords):
            _ = System.stderr.buffer.write(b"batch crash diagnostic: member failure\n")
            _ = System.stderr.buffer.flush()
            System.exit(7)
        StartedFile = JobRecords[0]["job"]["options"].get("started_file")
        if StartedFile:
            _ = FilePath(StartedFile).write_text(
                str(OsLayer.getpid()), encoding="ascii"
            )
        MemoryBlock = (
            b"x"
            * max(
                int(JobInfo["job"]["options"].get("memory_mib", 0))
                for JobInfo in JobRecords
            )
            * 1048576
        )
        assert not MemoryBlock or MemoryBlock[0] == 120
        TimeClock.sleep(
            max(
                float(JobInfo["job"]["options"].get("hold_seconds", 0))
                for JobInfo in JobRecords
            )
        )
    for MemberRoot in MemberRoots:
        WriteMember(MemberRoot)


if __name__ == "__main__":
    RunBatch(FilePath(System.argv[1]))
