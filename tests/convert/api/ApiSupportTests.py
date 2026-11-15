from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from tests.convert.api.ApiTestPaths import KSamplePath


def CheckSupport(TmpPath: FilePath) -> None:
    Document = OpenDocument(KSamplePath)
    Document.assert_valid()
    assert Document.source.format_id == "solidworks.sldprt"
    assert Document.sketches and Document.feature_timeline
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing destination")
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = WriteDocument(Document, TargetPath, overwrite=True)
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = ConvertFile(KSamplePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing destination"
