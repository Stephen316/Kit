from hashlib import sha256 as HashBytes
from io import BytesIO as ByteStream
from json import dumps as DumpJson, loads as LoadJson
from typing import cast as CastValue

from convert import open_document as OpenDocument, write_document as WriteDocument
from interchange import CadDocument
from tests.convert.api.Fusion.Native.VendorCases import KVendorCases, VendorSource


def TestLegacyWorld() -> None:
    CaseValue = KVendorCases[1]
    Document = OpenDocument(VendorSource(CaseValue))
    Encoded = CastValue(object, LoadJson(Document.to_json()))
    assert DropWorldMut(Encoded) > 0
    Restored = CadDocument.from_json(DumpJson(Encoded))
    Target = ByteStream()
    _ = WriteDocument(Restored, Target, destination_format="f3d", allow_carrier=False)
    assert HashBytes(Target.getvalue()).hexdigest() == CaseValue.OutputDigest


def DropWorldMut(Value: object) -> int:
    Count = 0
    if isinstance(Value, dict):
        Fields = CastValue(dict[str, object], Value)
        if (
            Fields.get("record")
            == "convert.formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld.SketchWorld"
        ):
            Members = CastValue(dict[str, object], Fields["fields"])
            for NameValue in ("RegularNodes", "NoCullingNodes"):
                assert Members[NameValue] == {"tuple": []}
                del Members[NameValue]
                Count += 1
        Count += sum(DropWorldMut(ItemValue) for ItemValue in Fields.values())
    elif isinstance(Value, list):
        Count += sum(
            DropWorldMut(ItemValue) for ItemValue in CastValue(list[object], Value)
        )
    return Count
