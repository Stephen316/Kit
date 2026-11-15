from dataclasses import replace as ReplaceData
from io import BytesIO as ByteStream
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.freecad.Adapter import FreeCadAdapter
from tests.convert.qualification.FreecadEvidence import FreecadEvidence
from tests.convert.qualification.TypedPart import TypedPart
from tests.convert.solidworks.core.NestedDocument import NestedDocument
from tests.convert.api.Fusion.AdapterCases import AdapterCase
from tests.interchange.fixtures.AssemblyFixture import BuildAssembly


@TestMark.parametrize("ModeValue", ("missing", "generic", "suppressed"))
@TestMark.parametrize("IsNested", (False, True))
def TestFreecadGate(TmpPath: FilePath, ModeValue: str, IsNested: bool) -> None:
    Document = FreecadEvidence(ModeValue)
    if IsNested:
        Document = NestedDocument(AdapterCase("parameter"), Document)
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    Reopened = OpenDocument(SourcePath)
    TargetPath = TmpPath / "Target.FCStd"
    _ = TargetPath.write_bytes(b"existing destination")
    with RaisesError(
        ValueError, match="FreeCAD cannot emit editable required features"
    ):
        _ = WriteDocument(
            Reopened, TargetPath, overwrite=True, validate=False, allow_carrier=True
        )
    assert TargetPath.read_bytes() == b"existing destination"
    Binary = ByteStream(b"existing stream")
    for Target in (TargetPath, Binary, TmpPath / "absent" / "Target.FCStd"):
        with RaisesError(
            ValueError, match="FreeCAD cannot emit editable required features"
        ):
            _ = FreeCadAdapter().write(
                Reopened, Target, WriteOptions(overwrite=True, validate=False)
            )
    assert TargetPath.read_bytes() == b"existing destination"
    assert Binary.getvalue() == b"existing stream"
    assert not (TmpPath / "absent").exists()
    assert not (TmpPath / "Target").exists()


def TestTypedPart(TmpPath: FilePath) -> None:
    Document = TypedPart()
    TargetPath = TmpPath / "Typed.FCStd"
    _ = FreeCadAdapter().write(Document, TargetPath)
    assert OpenDocument(TargetPath).feature_timeline == Document.feature_timeline


def TestTypedAsm(TmpPath: FilePath) -> None:
    Document = BuildAssembly()
    Assembly = Document.assembly
    assert Assembly is not None
    Assembly = ReplaceData(
        Assembly, documents=(ReplaceData(Assembly.documents[0], document=TypedPart()),)
    )
    Document = ReplaceData(Document, assembly=Assembly)
    TargetPath = TmpPath / "TypedAssembly.FCStd"
    _ = FreeCadAdapter().write(Document, TargetPath)
    assert OpenDocument(TargetPath).assembly == Document.assembly
