from json import loads as LoadJson
from pathlib import Path as FilePath
from shutil import which as FindProgram
from subprocess import run as RunProcess

from pytest import mark as TestMark

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.CliProcess import CliProcess


# installed entry points must expose actual format capabilities before users attempt conversion
def CheckCliCatalog(TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, "formats", "--json")
    assert Result.returncode == 0, Result.stderr
    Formats = {Value["format"]: Value for Value in LoadJson(Result.stdout)}
    assert Formats["solidworks.sldprt"]["read"] is True
    assert Formats["solidworks.sldprt"]["write"] is False
    assert Formats["fusion.f3d"]["write"] is True
    assert Formats["interchange.json"]["write"] is True
    Console = FindProgram("kit")
    assert Console is not None
    HelpResult = RunProcess(
        (Console, "--help"),
        cwd=TmpPath,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert HelpResult.returncode == 0, HelpResult.stderr
    assert "convert" in HelpResult.stdout and "decode" in HelpResult.stdout


# qualified native conversion must publish neutral data with explicit overwrite and source preservation
def CheckCliConvert(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.f3d"
    Original = EmitDocument(
        DocumentSpec(
            "CLI rectangle",
            "length",
            12.0,
            ProfileKind="rectangle",
            ConstrainRectangle=True,
        )
    )
    _ = Source.write_bytes(Original)
    Target = TmpPath / "decoded.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    Report = LoadJson(Result.stdout)
    assert Report["source_format"] == "fusion.f3d"
    assert Report["destination_format"] == "interchange.json"
    assert Report["dropped"] == [] and Report["requirements"] == []
    assert Report["application_usable"] is True
    assert CadDocument.from_json(Target.read_text()).Source.FormatId == "fusion.f3d"
    Before = Target.read_bytes()
    Repeated = CliProcess(TmpPath, "convert", str(Source), str(Target))
    assert Repeated.returncode == 1 and Target.read_bytes() == Before
    Overwrite = CliProcess(TmpPath, "convert", str(Source), str(Target), "--overwrite")
    assert Overwrite.returncode == 0, Overwrite.stderr
    assert "Writer evidence only" in Overwrite.stdout
    assert Source.read_bytes() == Original


# the public cli must preserve dimension driven cuboid bytes across a native neutral roundtrip
def CheckCliRound(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.f3d"
    Original = EmitDocument(
        DocumentSpec(
            "CLI cuboid", "height", 17.0, ProfileKind="cuboid", ConstrainRectangle=True
        )
    )
    _ = Source.write_bytes(Original)
    Neutral = TmpPath / "neutral.json"
    First = CliProcess(TmpPath, "convert", str(Source), str(Neutral), "--json")
    assert First.returncode == 0, First.stderr
    assert LoadJson(First.stdout)["source_format"] == "fusion.f3d"
    assert LoadJson(First.stdout)["destination_format"] == "interchange.json"
    Restored = TmpPath / "restored.f3d"
    Second = CliProcess(
        TmpPath,
        "convert",
        str(Neutral),
        str(Restored),
        "--from",
        "interchange.json",
        "--to",
        "f3d",
        "--json",
    )
    assert Second.returncode == 0, Second.stderr
    assert LoadJson(Second.stdout)["source_format"] == "interchange.json"
    assert LoadJson(Second.stdout)["destination_format"] == "fusion.f3d"
    assert Restored.read_bytes() == Original
    assert Source.read_bytes() == Original


# material and usability refusals must preserve user files at their respective writer boundaries
@TestMark.parametrize("HasMaterials", (False, True))
def CheckCliPolicy(HasMaterials: bool, TmpPath: FilePath) -> None:
    Source = TmpPath / "source.json"
    Document = MakeFusionDoc(
        DocumentSpec(
            "CLI policy",
            "height",
            17.0,
            ProfileKind="cuboid" if HasMaterials else "rectangle",
            ConstrainRectangle=True,
        )
    )
    Document.AssertValid()
    assert Document.sketches and Document.feature_timeline
    assert bool(Document.materials) is HasMaterials
    Original = Document.to_json()
    _ = Source.write_text(Original)
    Target = TmpPath / "blocked.CATPart"
    _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    if HasMaterials:
        assert Error["error"] == "ValueError"
        assert Error["message"].endswith(
            "does not support typed material density and color"
        )
        assert "details" not in Error
    else:
        assert "details" in Error, Error
        assert Error["details"]["code"] == "output_not_application_usable"
    assert Target.read_bytes() == b"existing output"
    assert Source.read_text() == Original
    assert sorted(Value.name for Value in TmpPath.iterdir()) == [
        "blocked.CATPart",
        "source.json",
    ]
