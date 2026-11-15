import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


def CheckOutcomes(CensusPath: FilePath, TempPath: FilePath) -> None:
    Report = JsonCodec.loads(CensusPath.read_text())
    assert len(Report["assets"]) == 714
    CheckArgs = [
        System.executable,
        str(FilePath(__file__).resolve().parents[2] / "re/automation/FusionCensus.py"),
        "check",
        "--expected",
        str(CensusPath),
        "--actual",
    ]
    SameRun = Subprocess.run(
        [*CheckArgs, str(CensusPath)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert SameRun.returncode == 0, SameRun.stderr
    for CaseName in ("missing", "improved", "duplicate", "source"):
        Changed = JsonCodec.loads(CensusPath.read_text())
        if CaseName == "missing":
            Changed["assets"] = Changed["assets"][1:]
        elif CaseName == "improved":
            AssetEntry = next(
                Entry for Entry in Changed["assets"] if Entry["outcome"] == "rejected"
            )
            AssetEntry.pop("reason")
            AssetEntry.update(
                outcome="decoded", reader_mode="strict", strict_rejection=None
            )
        elif CaseName == "duplicate":
            Changed["assets"].append(Changed["assets"][0])
        else:
            Changed["observation"]["manifest_sha256"] = "0" * 64
        ChangedPath = TempPath / f"{CaseName}.json"
        ChangedPath.write_text(JsonCodec.dumps(Changed))
        ChangedRun = Subprocess.run(
            [*CheckArgs, str(ChangedPath)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert ChangedRun.returncode == (
            3 if CaseName in ("missing", "improved") else 1
        ), ChangedRun.stderr
