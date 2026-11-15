import hashlib as Hashlib
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest


# each command compares saved archive records with pinned independent application measurements
@Pytest.mark.parametrize(
    ("ScriptPath", "Options", "ReportDigest"),
    (
        Pytest.param(
            "re/solidworks/archive/RectangularPlaneEvidence.py",
            ("--through-operation", "--include-coincidence"),
            "33c94376c4e892b93cf7046f62a6ea0a25d32876f147fd49bf5b217e1edb82a4",
            id="solidworks-p01-p03-resolved-list",
        ),
        Pytest.param(
            "re/solidworks/archive/ResolvedEntry.py",
            ("--through-operation",),
            "9ecde927c05c451e4f703eaf101748d75165d0a80d5f6db5f12a3615a328f257",
            id="solidworks-p04-resolved-list",
        ),
        Pytest.param(
            "re/solidworks/archive/SketchEvidence.py",
            ("--include-coincidence",),
            "d339efac5b24a262f50fe343d778349627d628cf9d09aa080c12461245bd3677",
            id="solidworks-p04-sketch-operands",
        ),
        Pytest.param(
            "re/automation/FusionRectangleSketchEvidence.py",
            (),
            "4781ee20a7a0d6d08ff9df4ee79bbcce19f6e527b3e9d9529796600e72abf1fa",
            id="fusion-p01-rectangle-operands",
        ),
        Pytest.param(
            "re/automation/FusionBossProfileEvidence.py",
            (),
            "8ed24ba6fa59486de3d34e8629221b43fc43e5f99f9b9530737eecf2d6c0fe14",
            id="fusion-p03-boss-profile",
        ),
        Pytest.param(
            "re/automation/FusionCutProfileEvidence.py",
            (),
            "52ff1ebd2b746ae50277fd9b49d18676fba0529d9c7289c4c8618a093392ac6a",
            id="fusion-p04-cut-profile",
        ),
        Pytest.param(
            "re/automation/FusionCutProjectionEvidence.py",
            (),
            "953d58343825f8e657b7fa4cafcf2513f99a96d6f1a948688904609536638cb8",
            id="fusion-p04-projected-edges",
        ),
        Pytest.param(
            "re/automation/FusionCutCenterEvidence.py",
            (),
            "21fdc6b688c7cddbb69546066903a8014d80c579e62a35c4dc522651425c4d51",
            id="fusion-p04-cut-center",
        ),
    ),
)
def CheckDiscoveryArchiveReport(
    ScriptPath: str, Options: tuple[str, ...], ReportDigest: str
) -> None:
    RepoPath = FilePath(__file__).resolve().parents[2]
    ResultInfo = Subprocess.run(
        [System.executable, "-B", ScriptPath, *Options],
        cwd=RepoPath,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr.decode(errors="replace")
    ActualDigest = Hashlib.sha256(ResultInfo.stdout).hexdigest()
    assert ActualDigest == ReportDigest, (ScriptPath, Options, ActualDigest)
