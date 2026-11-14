from dataclasses import replace as ReplaceData
from io import BytesIO as ByteStream
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.adapters import AdapterNotFoundError
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.api.Fusion.AlterDocument import AlterDocument
from tests.convert.api.Fusion.Native.ChangeNative import ChangeNative, KNativeChanges
from tests.convert.api.Fusion.Native.VendorCases import KVendorCases, VendorSource


@MarkTests.parametrize("RoleName", (*KNativeChanges, "body", "operation", "secondary"))
def TestVendorLinks(TmpPath: FilePath, RoleName: str) -> None:
    Source = VendorSource(KVendorCases[0])
    Document = OpenDocument(Source)
    Changed = ChangeNative(ReadDocument(Source.read_bytes()), RoleName)
    Archive = EmitParsed(Changed)
    with RaisesError(ValueError):
        _ = OpenDocument(ByteStream(Archive), source_format="f3d")
    Altered = ReplaceData(
        Document,
        metadata={"fusion.native_state": {"version": 2, "model": EncodeState(Changed)}},
    )
    Target = TmpPath / "Preserved.f3d"
    _ = Target.write_bytes(b"preserved destination")
    with RaisesError(ValueError):
        _ = WriteDocument(Altered, Target, destination_format="f3d", overwrite=True)
    assert Target.read_bytes() == b"preserved destination"
    assert tuple(TmpPath.iterdir()) == (Target,)


@MarkTests.parametrize(
    "FieldName", ("parameter", "material", "body", "history", "metadata")
)
def TestVendorGate(FieldName: str) -> None:
    Document = OpenDocument(VendorSource(KVendorCases[1]))
    Changed = AlterDocument(Document, FieldName)
    Target = ByteStream(b"preserved stream")
    ErrorType = AdapterNotFoundError if FieldName == "metadata" else ValueError
    with RaisesError(ErrorType):
        _ = WriteDocument(Changed, Target, destination_format="f3d")
    assert Target.getvalue() == b"preserved stream"
