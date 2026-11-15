from dataclasses import replace as ReplaceData
from io import BytesIO as ByteStream, StringIO as TextStream
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.base.WriteOptions import WriteOptions
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.solidworks.core.DirectWriters import KDirectWriters
from tests.convert.solidworks.core.MarkedDocument import MarkedDocument
from tests.convert.solidworks.core.NestedDocument import NestedDocument


@TestMark.parametrize(
    ("GuardCase", "ErrorText"),
    (
        ("research", "unqualified research documents"),
        ("inch", "unresolved SOLIDWORKS inch dimensions"),
        ("reference", "unresolved SOLIDWORKS equation references"),
        ("target", "unresolved SOLIDWORKS equation references"),
    ),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("RelabelSource", (False, True))
def TestDirectWrite(
    TmpPath: FilePath,
    GuardCase: str,
    ErrorText: str,
    IsNested: bool,
    RelabelSource: bool,
) -> None:
    Original = OpenDocument(KSamplePath)
    if RelabelSource:
        Original = ReplaceData(
            Original, source=ReplaceData(Original.source, format_id="interchange.json")
        )
    Marked = MarkedDocument(Original, GuardCase)
    Document = NestedDocument(Original, Marked) if IsNested else Marked
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    Document = OpenDocument(SourcePath)
    for WriteName, WriteAction in KDirectWriters:
        TargetPath = TmpPath / f"{WriteName}.json"
        _ = TargetPath.write_bytes(b"existing destination")
        with RaisesError(ValueError, match=ErrorText):
            _ = WriteAction(
                Document, TargetPath, WriteOptions(overwrite=True, validate=False)
            )
        assert TargetPath.read_bytes() == b"existing destination"
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
