from pathlib import Path as FilePath

from tests.Convert.Runtime.WheelBuild import BuildWheel
from tests.Convert.Runtime.WheelExecute import RunIsolated
from tests.Convert.Runtime.WheelInspect import ExtractWheel


# built distribution behavior must match source behavior with every external hook blocked
def CheckWheel(TmpPath: FilePath) -> None:
    WheelPath = BuildWheel(TmpPath)
    InstallRoot = TmpPath / "site"
    ExtractWheel(WheelPath, InstallRoot)
    RuntimeResult = RunIsolated(TmpPath, InstallRoot)
    assert RuntimeResult.returncode == 0, RuntimeResult.stderr
