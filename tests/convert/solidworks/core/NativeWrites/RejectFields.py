from dataclasses import replace as ReplaceData
from io import BytesIO as ByteStream
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import convert as ConvertFile
from convert import write_document as WriteDocument
from interchange.document.models.DocumentError import DocumentError
from interchange.document.models.DocumentModel import CadDocument
from interchange.serialization.JsonCodec import LoadJson
from tests.convert.api.Fusion.AdapterCases import AdapterCase
from tests.convert.solidworks.core.NestedDocument import NestedDocument
from tests.convert.solidworks.core.RejectWrites import RejectWrites


def RejectFields(Document: CadDocument, TmpPath: FilePath, IsNested: bool) -> None:
    Document = ReplaceData(
        Document,
        source=ReplaceData(Document.source, format_id="json", path="relabeled.json"),
    )
    if IsNested:
        Document = NestedDocument(AdapterCase("rectangle"), Document)
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    Restored = LoadJson(SourcePath.read_text(encoding="utf-8"))
    assert isinstance(Restored, CadDocument)
    assert Restored == Document
    Document = Restored
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing public destination")
    ErrorText = "native or unresolved required semantics"
    with RaisesError(ValueError, match=ErrorText):
        _ = WriteDocument(Document, TargetPath, overwrite=True, validate=False)
    if Document.validate():
        with RaisesError(DocumentError):
            _ = ConvertFile(SourcePath, TargetPath, overwrite=True, strict=False)
    else:
        with RaisesError(ValueError, match=ErrorText):
            _ = ConvertFile(SourcePath, TargetPath, overwrite=True, strict=False)
    assert TargetPath.read_bytes() == b"existing public destination"
    Output = ByteStream(b"existing public stream")
    with RaisesError(ValueError, match=ErrorText):
        _ = WriteDocument(
            Document, Output, destination_format="interchange.json", validate=False
        )
    assert Output.getvalue() == b"existing public stream"
    RejectWrites(Document, TmpPath, ErrorText)
