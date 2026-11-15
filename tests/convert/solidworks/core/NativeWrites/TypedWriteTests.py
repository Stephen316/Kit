from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.Fusion.AdapterCases import AdapterCase


def TestTypedWrite(TmpPath: FilePath) -> None:
    Document = CadDocument.from_json(AdapterCase("cuboid").to_json())
    assert Document.sketches[0].constraints
    TargetPath = TmpPath / "Typed.f3d"
    _ = WriteDocument(Document, TargetPath, allow_carrier=False)
    Parsed = OpenDocument(TargetPath)
    assert Parsed.sketches == Document.sketches
    assert len(Parsed.feature_timeline) == len(Document.feature_timeline)
