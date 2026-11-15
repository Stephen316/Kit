from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from tests.convert.api.ApiTestPaths import KSamplePath


@TestMark.parametrize("SourceCase", ("missing", "unknown", "unframed"))
def TestSupportData(TmpPath: FilePath, SourceCase: str) -> None:
    Original = OpenDocument(KSamplePath)
    Sketch, *Remaining = Original.sketches
    Attributes = dict(Sketch.attributes)
    if SourceCase == "missing":
        del Attributes["support_plane_source"]
    elif SourceCase == "unknown":
        Attributes["support_plane_source"] = "unknown"
    else:
        Attributes["unframed_support_plane_native_id"] = Attributes[
            "support_plane_native_id"
        ]
    Document = ReplaceData(
        Original,
        sketches=(ReplaceData(Sketch, attributes=Attributes), *Remaining),
    )
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing destination")
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = WriteDocument(OpenDocument(SourcePath), TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing destination"
