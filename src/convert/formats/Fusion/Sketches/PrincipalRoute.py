from convert.formats.Fusion.Extrudes.Plane.OffsetBackend import KOffsetBackend
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf


# placement alone cannot distinguish origin plane attachment from a coincident face
def PrincipalRoute(
    BulkData: bytes, Owners: dict[int, RecordSpan], Feature: RecordSpan
) -> tuple[int, int, int, int]:
    FeatureBody = BulkData[Feature.PayloadOffset + 4 : Feature.EndOffset]
    if len(FeatureBody) != 293:
        raise ValueError("Unsupported Fusion principal sketch feature extent")
    FeatureWire = MetaCursor(FeatureBody)
    FeatureWire.Offset = 45
    ControllerId = ReadNativeRef(FeatureWire)
    FeatureWire.Offset = 147
    if FeatureWire.ReadWord() != 4:
        raise ValueError("Unsupported Fusion principal sketch dependency count")
    DescriptorId = ReadNativeRef(FeatureWire)
    if ReadNativeRef(FeatureWire) != ControllerId:
        raise ValueError("Fusion principal sketch controller copies disagree")
    Controller = SelectCursor(BulkData, Owners, ControllerId, KOffsetBackend)
    ControllerSize = len(Controller.DataValue)
    if ControllerSize not in (187, 315):
        raise ValueError("Unsupported Fusion principal sketch controller extent")
    Controller.Offset = ControllerSize - 103
    if Controller.ReadWord() != 1 or ReadNativeRef(Controller) != DescriptorId:
        raise ValueError("Fusion principal sketch descriptor copies disagree")
    Controller.Offset = ControllerSize - 11
    if ReadNativeRef(Controller) != Feature.ObjectId:
        raise ValueError("Fusion principal sketch controller owner disagrees")
    LeafId = ReadDescLeaf(BulkData, Owners, DescriptorId, Feature.ObjectId)
    return ControllerId, DescriptorId, LeafId, ReadEntityLeaf(BulkData, Owners, LeafId)
