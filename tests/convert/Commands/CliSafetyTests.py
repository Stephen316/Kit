from json import loads as LoadJson
from os.path import relpath as RelativePath
from pathlib import Path as FilePath
from struct import pack_into as PackInto
from subprocess import run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform

from pytest import mark as TestMark

from convert.adapters.solidworks.container.Container import BuildSldprt
from convert.adapters.solidworks.container.Container import (
    KLocalSignaturePrefix,
    KLocalSignatureSize,
)
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.formats.FusionHistoryTests import HistoryArchive


@TestMark.parametrize("Command", ("convert", "decode"))
def CheckHomeAlias(Command: str, TmpPath: FilePath) -> None:
    Source = TmpPath / "source.SLDPRT"
    Original = KSamplePath.read_bytes()
    _ = Source.write_bytes(Original)
    Target = "~/" + RelativePath(Source, FilePath.home())
    Arguments = (Target,) if Command == "convert" else ("-o", Target)
    Result = CliProcess(TmpPath, Command, str(Source), *Arguments, "--overwrite")
    assert Result.returncode == 1 and "different files" in Result.stderr
    assert Source.read_bytes() == Original
    ReadHome = CliProcess(TmpPath, "decode", Target, "--layer", "container")
    assert ReadHome.returncode == 0, ReadHome.stderr


@TestMark.skipif(KPlatform == "win32", reason="POSIX permission contract")
def CheckDecodeMode(TmpPath: FilePath) -> None:
    Target = TmpPath / "decoded.json"
    Result = RunProcess(
        (KPythonPath, "-m", "convert", "decode", str(KSamplePath), "-o", str(Target)),
        cwd=TmpPath,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
        umask=0o027,
    )
    assert Result.returncode == 0, Result.stderr
    assert Target.stat().st_mode & 0o777 == 0o640
    Target.chmod(0o600)
    Repeated = CliProcess(
        TmpPath, "decode", str(KSamplePath), "-o", str(Target), "--overwrite"
    )
    assert Repeated.returncode == 0, Repeated.stderr
    assert Target.stat().st_mode & 0o777 == 0o600
    assert not list(TmpPath.glob(".kit-*"))


def CheckSwBound(TmpPath: FilePath) -> None:
    Source = TmpPath / "oversized.SLDPRT"
    Payload = bytearray(BuildSldprt({"Header2": b"data"}))
    Offset = Payload.find(KLocalSignaturePrefix)
    PackInto("<I", Payload, Offset + KLocalSignatureSize + 8, 128 * 1024 * 1024 + 1)
    _ = Source.write_bytes(Payload)
    for Arguments in ((), ("--stream", "Header2")):
        Result = CliProcess(
            TmpPath, "decode", str(Source), "--layer", "container", *Arguments
        )
        assert Result.returncode == 1 and "decoded size limit" in Result.stderr
        assert Result.stdout == "" and "Traceback" not in Result.stderr


def CheckPartialUse(TmpPath: FilePath) -> None:
    Source = TmpPath / "partial.f3d"
    _ = Source.write_bytes(HistoryArchive())
    Target = TmpPath / "partial.json"
    Result = CliProcess(TmpPath, "decode", str(Source), "--partial", "-o", str(Target))
    assert Result.returncode == 0, Result.stderr
    Report = LoadJson(Target.read_text())
    assert Report["kind"] == "kit.decode" and Report["partial"] is True
    assert "fusion.history.partial" in Target.read_text()
    Converted = TmpPath / "converted.json"
    Conversion = CliProcess(TmpPath, "convert", str(Target), str(Converted), "--json")
    assert Conversion.returncode == 1 and not Converted.exists()
    assert "Traceback" not in Conversion.stderr
