from io import BytesIO as ByteStream
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters import AdapterNotFoundError
from tests.convert.api.Fusion.AdapterCases import AdapterCase
from tests.convert.api.Fusion.AlterDocument import AlterDocument


@MarkTests.parametrize(
    "FieldName", ("parameter", "material", "body", "history", "metadata", "source")
)
def TestAuthorGate(TmpPath: FilePath, FieldName: str) -> None:
    Document = AlterDocument(AdapterCase("extrusion"), FieldName)
    Target = TmpPath / "Rejected.f3d"
    _ = Target.write_bytes(b"preserved destination")
    with RaisesError((ValueError, AdapterNotFoundError)):
        _ = WriteDocument(Document, Target, destination_format="f3d", overwrite=True)
    assert Target.read_bytes() == b"preserved destination"
    assert tuple(TmpPath.iterdir()) == (Target,)


@MarkTests.parametrize(
    "FieldName", ("parameter", "material", "body", "history", "metadata")
)
def TestNativeGate(TmpPath: FilePath, FieldName: str) -> None:
    Source = TmpPath / "Source.f3d"
    _ = WriteDocument(AdapterCase("cuboid"), Source, destination_format="f3d")
    Document = AlterDocument(OpenDocument(Source), FieldName)
    Target = ByteStream(b"preserved stream")
    with RaisesError((ValueError, AdapterNotFoundError)):
        _ = WriteDocument(Document, Target, destination_format="f3d")
    assert Target.getvalue() == b"preserved stream"
