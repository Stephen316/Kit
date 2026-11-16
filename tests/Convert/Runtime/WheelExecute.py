from pathlib import Path as FilePath
import subprocess as ProcessLib
import sys as SystemLib

from tests.Convert.Formats.FusionHistoryTests import HistoryArchive
from tests.Convert.Runtime.IsolatedRuntime import KIsolatedRuntime
from tests.Convert.Runtime.RuntimeRules import KRootPath


# isolated execution proves the built wheel cannot reach external runtime hooks
def RunIsolated(
    TmpPath: FilePath, InstallRoot: FilePath
) -> ProcessLib.CompletedProcess[str]:
    OutputFolder = TmpPath / "runtime"
    OutputFolder.mkdir()
    _ = (OutputFolder / "runtime-fusion.f3d").write_bytes(HistoryArchive())
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
