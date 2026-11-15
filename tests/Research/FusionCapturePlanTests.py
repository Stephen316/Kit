import hashlib as Hashing
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest


@Pytest.mark.parametrize("RecipeId", ("P01", "P05"))
def CheckPlanPins(RecipeId: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    with TempFiles.TemporaryDirectory() as TempPath:
        OutputPath = FilePath(TempPath) / "Capture"
        Result = Subprocess.run(
            [
                System.executable,
                str(RootPath / "re/automation/PairedCaptures/FusionFreshProcess.py"),
                "--output",
                str(OutputPath),
                "--recipe",
                RecipeId,
                "--read-existing",
            ],
            cwd=RootPath,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if RecipeId == "P05":
            assert Result.returncode == 2, Result.stderr
            assert not OutputPath.exists()
            return
        assert Result.returncode == 0, Result.stderr
        PlanInfo = JsonCodec.loads((OutputPath / "plan.json").read_bytes())
        BindingPath = "re/automation/PairedCaptures/FusionBindings.py"
        BindingData = (RootPath / BindingPath).read_bytes()
        assert PlanInfo["pins"]["bindings"] == {
            "path": BindingPath,
            "sha256": Hashing.sha256(BindingData).hexdigest(),
            "size_bytes": len(BindingData),
        }
        assert PlanInfo["recipes"] == ["P01"]
        assert set(PlanInfo["existing"]["P01"]["archives"]) == {"a", "b"}
        for PhaseName in ("a", "b"):
            assert (OutputPath / f"phase-{PhaseName}.py").is_file()
            assert not (OutputPath / f"phase-{PhaseName}").exists()
