from base64 import b64decode as DecodeBase
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import version_info as KPythonVersion
from zipfile import ZipFile

from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess


# developer decoding must provide stable neutral inspection through both stdout and file publication
def CheckCliNeutral(TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, "decode", str(KSamplePath))
    assert Result.returncode == 0, Result.stderr
    Decoded = LoadJson(Result.stdout)
    assert (
        CadDocument.from_json(
            DumpJson(LoadJson(Result.stdout)["document"])
        ).Source.FormatId
        == "solidworks.sldprt"
    )
    Target = TmpPath / "decode.json"
    Saved = CliProcess(TmpPath, "decode", str(KSamplePath), "-o", str(Target))
    assert Saved.returncode == 0 and Saved.stdout == "", Saved.stderr
    assert LoadJson(Target.read_text()) == Decoded
    Before = Target.read_bytes()
    Repeated = CliProcess(TmpPath, "decode", str(KSamplePath), "-o", str(Target))
    assert Repeated.returncode == 1 and Target.read_bytes() == Before
    Overwrite = CliProcess(
        TmpPath, "decode", str(KSamplePath), "-o", str(Target), "--overwrite"
    )
    assert Overwrite.returncode == 0, Overwrite.stderr
    assert LoadJson(Target.read_text()) == Decoded
    assert not list(TmpPath.glob(".kit-*"))


# container inspection must expose exact stream bytes and refuse nonexistent members cleanly
def CheckSwStream(TmpPath: FilePath) -> None:
    Result = CliProcess(
        TmpPath,
        "decode",
        str(KSamplePath),
        "--layer",
        "container",
        "--stream",
        "Header2",
    )
    assert Result.returncode == 0, Result.stderr
    Report = LoadJson(Result.stdout)
    assert Report["layer"] == "container" and Report["members"]
    assert DecodeBase(Report["stream"]["data"]) == SldprtArchive.OpenAction(
        KSamplePath
    ).Require("Header2")
    Missing = CliProcess(
        TmpPath,
        "decode",
        str(KSamplePath),
        "--layer",
        "container",
        "--stream",
        "missing",
    )
    assert Missing.returncode == 1 and Missing.stdout == ""


# fusion container and native inspection must respect the runtime required for archive extraction
def CheckFusViews(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.f3d"
    _ = Source.write_bytes(EmitDocument(DocumentSpec("CLI parameter", "height", 19.0)))
    Inventory = CliProcess(TmpPath, "decode", str(Source), "--layer", "container")
    assert Inventory.returncode == 0, Inventory.stderr
    Report = LoadJson(Inventory.stdout)
    StreamName = next(
        Value["name"] for Value in Report["members"] if not Value["directory"]
    )
    Stream = CliProcess(
        TmpPath, "decode", str(Source), "--layer", "container", "--stream", StreamName
    )
    Native = CliProcess(TmpPath, "decode", str(Source), "--layer", "native")
    if KPythonVersion < (3, 14):
        assert Stream.returncode == 1 and "Python 3.14" in Stream.stderr
        assert Native.returncode == 1 and "Python 3.14" in Native.stderr
        return
    assert Stream.returncode == 0, Stream.stderr
    with ZipFile(Source) as Archive:
        assert DecodeBase(LoadJson(Stream.stdout)["stream"]["data"]) == Archive.read(
            StreamName
        )
    assert Native.returncode == 0, Native.stderr
    State = LoadJson(Native.stdout)
    assert State["record"].endswith("DocumentModel.DocumentModel")
    assert State["fields"]["Segments"]["tuple"]


# explicit partial inspection must remain usable for supported documents without changing their format identity
def CheckCliPartial(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.f3d"
    _ = Source.write_bytes(EmitDocument(DocumentSpec("CLI parameter", "height", 19.0)))
    Result = CliProcess(TmpPath, "decode", str(Source), "--partial")
    assert Result.returncode == 0, Result.stderr
    assert (
        CadDocument.from_json(
            DumpJson(LoadJson(Result.stdout)["document"])
        ).Source.FormatId
        == "fusion.f3d"
    )
