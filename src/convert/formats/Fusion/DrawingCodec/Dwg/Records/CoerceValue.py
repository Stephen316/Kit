from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord, KDwgValue


def AsInt(Value: KDwgValue) -> int:
    if isinstance(Value, int):
        return Value
    raise ValueError("DWG record value is not an integer")


def AsFloat(Value: KDwgValue) -> float:
    if isinstance(Value, (int, float)):
        return float(Value)
    raise ValueError("DWG record value is not a number")


def AsText(Value: KDwgValue) -> str:
    if isinstance(Value, str):
        return Value
    raise ValueError("DWG record value is not text")


def AsBytes(Value: KDwgValue) -> bytes:
    if isinstance(Value, bytes):
        return Value
    raise ValueError("DWG record value is not a byte string")


def AsHandle(Value: KDwgValue) -> DwgHandleRef:
    if isinstance(Value, DwgHandleRef):
        return Value
    raise ValueError("DWG record value is not a handle reference")


def AsPoint(Value: KDwgValue, Count: int) -> tuple[float, ...]:
    if not isinstance(Value, tuple) or len(Value) != Count:
        raise ValueError(f"DWG record value is not a {Count} coordinate point")
    Points = tuple(
        float(Element) for Element in Value if isinstance(Element, (int, float))
    )
    if len(Points) != Count:
        raise ValueError("DWG record point holds a non numeric coordinate")
    return Points


def AsHandles(Value: KDwgValue) -> tuple[DwgHandleRef, ...]:
    if not isinstance(Value, tuple):
        raise ValueError("DWG record value is not a handle list")
    Handles = tuple(Element for Element in Value if isinstance(Element, DwgHandleRef))
    if len(Handles) != len(Value):
        raise ValueError("DWG record handle list holds another value kind")
    return Handles


def AsRecords(Value: KDwgValue) -> tuple[DwgRecord, ...]:
    if not isinstance(Value, tuple):
        raise ValueError("DWG record value is not a record list")
    Records = tuple(Element for Element in Value if isinstance(Element, DwgRecord))
    if len(Records) != len(Value):
        raise ValueError("DWG record list holds another value kind")
    return Records


def AsRecord(Value: KDwgValue) -> DwgRecord:
    if isinstance(Value, DwgRecord):
        return Value
    raise ValueError("DWG record value is not a nested record")
