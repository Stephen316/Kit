from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# the mat json contract needs boundary coverage so stored document relationships remain consistent
def TestMatJson(TmpPath: FilePath) -> None:
    Document = AdapterCase("cuboid")
    Target = TmpPath / "Neutral.json"
    _ = WriteDocument(Document, Target, destination_format="interchange.json")
    Restored = OpenDocument(Target)
    assert Restored.materials == Document.materials
    assert Restored == Document


# the mat gate contract needs boundary coverage so stored document relationships remain consistent
def TestMatGate(TmpPath: FilePath) -> None:
    Document = AdapterCase("cuboid")
    Target = TmpPath / "Legacy.FCStd"
    _ = Target.write_bytes(b"existing document")
    with RaisesError(ValueError, match="typed material density and color"):
        _ = WriteDocument(
            Document, Target, destination_format="freecad.fcstd", overwrite=True
        )
    assert Target.read_bytes() == b"existing document"
    assert tuple(TmpPath.iterdir()) == (Target,)
