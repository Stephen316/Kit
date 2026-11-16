from convert.Formats.Fusion.BodyInputs.BodyInput import BodyInputs
from convert.Formats.Fusion.BodyInputs.InputRefs import ReadInputPicks
from convert.Formats.Fusion.BodyInputs.ScaleControls import ReadScaleData
from convert.Formats.Fusion.RecordSpan import RecordSpan


# the authored list follows a validated uniform or per axis factor layout
def ReadScaleInputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> BodyInputs:
    Fields = ReadScaleData(BulkData, Owners, FeatureId)
    return BodyInputs(
        ReadInputPicks(BulkData, Owners, FeatureId, Fields.ProxyId, "input", 4)
    )
