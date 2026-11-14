from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess


def CheckAsmLabel(TmpPath: FilePath) -> None:
    Source = (
        KSamplePath.parents[1]
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "Cylinder Head Assy 1.SLDASM"
    )
    Result = CliProcess(TmpPath, "decode", str(Source), "--layer", "container")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)["format"] == "solidworks.sldasm"
    Renamed = TmpPath / "assembly.data"
    _ = Renamed.write_bytes(Source.read_bytes())
    Explicit = CliProcess(
        TmpPath,
        "decode",
        str(Renamed),
        "--layer",
        "container",
        "--from",
        "solidworks.sldasm",
    )
    assert Explicit.returncode == 0, Explicit.stderr
    assert LoadJson(Explicit.stdout)["format"] == "solidworks.sldasm"
