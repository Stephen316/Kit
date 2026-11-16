from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.json.Adapter import JsonAdapter
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# resolved portable support should preserve ordinary native writing and interchange serialization
def TestSafeSupport(TmpPath: FilePath) -> None:
    Original = AdapterCase("rectangle")
    NativePath = TmpPath / "Rectangle.f3d"
    _ = WriteDocument(
        Original, NativePath, destination_format="f3d", allow_carrier=False
    )
    Document = OpenDocument(NativePath)
    assert Document.sketches
    assert all(
        "support_plane_source" not in Sketch.attributes
        and "support_plane_native_id" not in Sketch.attributes
        and "unframed_support_plane_native_id" not in Sketch.attributes
        for Sketch in Document.sketches
    )
    TargetPath = TmpPath / "Direct.json"
    _ = JsonAdapter().write(Document, TargetPath, WriteOptions())
    assert OpenDocument(TargetPath) == Document
    PublicPath = TmpPath / "Public.json"
    _ = WriteDocument(Document, PublicPath)
    assert OpenDocument(PublicPath) == Document
