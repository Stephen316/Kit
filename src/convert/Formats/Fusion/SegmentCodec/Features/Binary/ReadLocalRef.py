from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the local reference operation needs a distinct decoding boundary so native records retain their segment ownership and schema
def ReadLocalRefMut(Cursor: MetaCursor) -> LocalRef | None:
    Marker = Cursor.TakeBytes(1)
    if Marker == b"\0":
        return None
    if Marker != b"\1":
        raise ValueError("Unsupported Fusion feature reference tag")
    Identity = Cursor.ReadLong()
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Fusion feature reference requires a local numeric target")
    return LocalRef(Identity)
