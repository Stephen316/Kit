from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# the auxiliary record independently identifies the feature receiving the controls
KExtrudeCache = "0897AF07-EF1B-42E5-BDD9-1C746A085CBC"


# the same two owner copies corroborate distance and cut control slots
def CheckExtCache(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int, CacheId: int
) -> None:
    Cache = SelectCursor(BulkData, Owners, CacheId, KExtrudeCache)
    if (
        len(Cache.DataValue) != 81
        or Cache.TakeBytes(2) != bytes(2)
        or ReadNativeRef(Cache) != FeatureId
    ):
        raise ValueError("Unsupported Fusion Extrude auxiliary cache prefix")
    Cache.Offset = 70
    if ReadNativeRef(Cache) != FeatureId:
        raise ValueError("Fusion Extrude auxiliary cache owner disagrees")
