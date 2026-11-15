import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Calibration.BuildManifest import BuildManifest
from tests.Research.Calibration.RunCalibration import KRepoRoot


# forbidden manifest work must fail before acquiring any private execution state
@TestMark.parametrize(
    "Invalid",
    ("dependency", "application", "model", "resource", "digest", "group", "reserve"),
)
def CheckRefusal(TmpPath: FilePath, Invalid: str) -> None:
    ManifestPath = BuildManifest(TmpPath)
    Manifest = JsonCodec.loads(ManifestPath.read_text(encoding="utf-8"))
    if Invalid == "dependency":
        Manifest["jobs"][0]["depends_on"] = ["live:external"]
    if Invalid in {"application", "model"}:
        Manifest["kind"] = (
            "fusion.application" if Invalid == "application" else "model.external"
        )
    if Invalid == "resource":
        Manifest["resources"] = {}
    if Invalid == "digest":
        Manifest["bindings"]["source:calibration"]["sha256"] = "f" * 64
    if Invalid == "group":
        Manifest["runner"]["group_protocol"] = 1
    if Invalid == "reserve":
        Manifest["reserved_cpus"] = 0
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    OutputPath = TmpPath / "Refused"
    Process = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Calibration.py"),
            "--manifest",
            str(ManifestPath),
            "--output",
            str(OutputPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 1
    assert not OutputPath.exists()
    assert "completed_sweep" in Process.stderr and "false" in Process.stderr
