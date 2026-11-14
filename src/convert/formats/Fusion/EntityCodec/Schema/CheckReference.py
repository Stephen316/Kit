from convert.formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def CheckReference(
    Value: KEntityValue, TargetGuid: str, Catalog: EntityCatalog
) -> None:
    if Value is None:
        return
    if isinstance(Value, LocalRef):
        Actual = Catalog.LocalClasses.get(Value.ObjectId)
    elif isinstance(Value, SegmentRef):
        Actual = Catalog.ExternalClasses.get((Value.SegmentId, Value.ObjectId))
    elif isinstance(Value, CrossRef):
        Actual = Value.TypeGuid.upper()
        if Actual not in Catalog.Classes:
            return
    else:
        raise ValueError("Fusion entity reference requires a typed target")
    if Actual is None:
        raise ValueError("Unresolved Fusion entity reference target")
    Expected = TargetGuid.upper()
    if not Expected or Expected == Catalog.RootGuid:
        return
    for _ in range(KMaxDepth):
        if Actual == Expected:
            return
        Schema = Catalog.Classes.get(Actual)
        if Schema is None or not Schema.BaseGuid:
            break
        Actual = Schema.BaseGuid.upper()
    raise ValueError("Fusion entity reference target class is incompatible")
