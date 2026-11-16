from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# a complete typed roundtrip verifies semantic checks allow editable native output
def TestTypedWrite(TmpPath: FilePath) -> None:
    Document = CadDocument.from_json(AdapterCase("cuboid").to_json())
    assert Document.sketches[0].constraints
    TargetPath = TmpPath / "Typed.f3d"
    _ = WriteDocument(Document, TargetPath, allow_carrier=False)
    Parsed = OpenDocument(TargetPath)
    assert Parsed.sketches == Document.sketches
    assert len(Parsed.feature_timeline) == len(Document.feature_timeline)
