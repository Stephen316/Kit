# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from pathlib import Path as FilePath

from tests.convert.runtime.WheelBuild import BuildWheel
from tests.convert.runtime.WheelExecute import RunIsolated
from tests.convert.runtime.WheelInspect import ExtractWheel


# built distribution behavior must match source behavior with every external hook blocked
def CheckWheel(TmpPath: FilePath) -> None:
    WheelPath = BuildWheel(TmpPath)
    InstallRoot = TmpPath / "site"
    ExtractWheel(WheelPath, InstallRoot)
    RuntimeResult = RunIsolated(TmpPath, InstallRoot)
    assert RuntimeResult.returncode == 0, RuntimeResult.stderr
