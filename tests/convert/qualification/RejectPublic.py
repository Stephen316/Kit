from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.solidworks.core.RejectWrites import RejectWrites


def RejectPublic(Document: CadDocument, TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    Reopened = OpenDocument(SourcePath)
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing public destination")
    for InputValue in (Document, Reopened):
        with RaisesError(ValueError, match="native or unresolved required semantics"):
            _ = WriteDocument(InputValue, TargetPath, overwrite=True, validate=False)
        assert TargetPath.read_bytes() == b"existing public destination"
    with RaisesError(ValueError, match="native or unresolved required semantics"):
        _ = ConvertFile(SourcePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing public destination"
    RejectWrites(Reopened, TmpPath, "native or unresolved required semantics")
