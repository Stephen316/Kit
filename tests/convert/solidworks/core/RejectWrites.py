from io import BytesIO as ByteStream, StringIO as TextStream
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert.adapters.base.WriteOptions import WriteOptions
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.solidworks.core.DirectWriters import KDirectWriters


# each writer refusal must preserve an existing destination and skip new output
def RejectWrites(Document: CadDocument, TmpPath: FilePath, ErrorText: str) -> None:
    for WriteName, WriteAction in KDirectWriters:
        DirectPath = TmpPath / f"{WriteName}.json"
        _ = DirectPath.write_bytes(b"existing direct destination")
        with RaisesError(ValueError, match=ErrorText):
            _ = WriteAction(
                Document, DirectPath, WriteOptions(overwrite=True, validate=False)
            )
        assert DirectPath.read_bytes() == b"existing direct destination"
        MissingPath = TmpPath / "absent" / WriteName / "Target.json"
        with RaisesError(ValueError, match=ErrorText):
            _ = WriteAction(Document, MissingPath, WriteOptions(validate=False))
        assert not MissingPath.parent.exists()
        Binary = ByteStream(b"existing bytes")
        with RaisesError(ValueError, match=ErrorText):
            _ = WriteAction(Document, Binary, WriteOptions(validate=False))
        assert Binary.getvalue() == b"existing bytes"
        Textual = TextStream("existing text")
        with RaisesError(ValueError, match=ErrorText):
            _ = WriteAction(Document, Textual, WriteOptions(validate=False))
        assert Textual.getvalue() == "existing text"
