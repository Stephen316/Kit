# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from pathlib import Path as FilePath
import shutil as ShutilLib
import subprocess as ProcessLib

from tests.convert.runtime.RuntimeRules import KRootPath


# isolated wheel checks need one reproducible offline build artifact
def BuildWheel(TmpPath: FilePath) -> FilePath:
    UvPath = ShutilLib.which("uv")
    assert UvPath is not None
    WheelFolder = TmpPath / "wheel"
    BuildResult = ProcessLib.run(
        (
            UvPath,
            "build",
            "--wheel",
            "--offline",
            "--no-progress",
            "--out-dir",
            str(WheelFolder),
        ),
        cwd=KRootPath,
        check=True,
        capture_output=True,
        text=True,
    )
    WheelPaths = tuple(WheelFolder.glob("*.whl"))
    assert BuildResult.returncode == 0
    assert len(WheelPaths) == 1
    return WheelPaths[0]
