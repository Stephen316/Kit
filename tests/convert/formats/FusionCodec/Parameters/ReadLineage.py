from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# shared read lineage setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadLineage(
    Classes: tuple[MetaClass, ...], ClassGuid: str
) -> tuple[ClassStamp, ...]:
    Registry = {Value.ClassGuid.upper(): Value for Value in Classes}
    Result: list[ClassStamp] = []
    Visited: set[str] = set()
    while ClassGuid:
        Identity = ClassGuid.upper()
        assert Identity not in Visited
        Visited.add(Identity)
        Value = Registry[Identity]
        Result.append(ClassStamp(Value.ClassGuid, Value.BaseGuid, Value.SchemaVersion))
        ClassGuid = Value.BaseGuid
    return tuple(Result)
