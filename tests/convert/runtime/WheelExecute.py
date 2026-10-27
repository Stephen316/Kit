# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from pathlib import Path as FilePath
import subprocess as ProcessLib
import sys as SystemLib

from tests.convert.runtime.IsolatedRuntime import KIsolatedRuntime
from tests.convert.runtime.RuntimeRules import KRootPath


# isolated execution proves the built wheel cannot reach external runtime hooks
def RunIsolated(
    TmpPath: FilePath, InstallRoot: FilePath
) -> ProcessLib.CompletedProcess[str]:
    OutputFolder = TmpPath / "runtime"
    OutputFolder.mkdir()
    return ProcessLib.run(
        (
            SystemLib.executable,
            "-I",
            "-S",
            "-c",
            KIsolatedRuntime,
            str(InstallRoot),
            str(KRootPath),
            str(OutputFolder),
        ),
        cwd=TmpPath,
        check=False,
        capture_output=True,
        text=True,
    )
