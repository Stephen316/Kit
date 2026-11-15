from convert.formats.Fusion.BodyInputs.ProxyInputCheck import CheckInputProxy
from convert.formats.Fusion.Extrudes.Plane.PlanePickSupport import KSketchFaceMode
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectIds, SelectCursor
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from convert.formats.Fusion.Sketches.SketchRuleIds import KSketchRoot


# the saved sketch root must own the body link and the feature that selected the face
def ReadFaceOwner(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchId: int, BodyId: int
) -> tuple[int, int, int]:
    Sketch = SelectCursor(BulkData, Owners, SketchId, KSketchRoot)
    if len(Sketch.DataValue) != 231:
        raise ValueError("Unsupported Fusion body supported sketch root")
    Sketch.Offset = 204
    if ReadNativeRef(Sketch) != BodyId or Sketch.TakeBytes(1) != b"\1":
        raise ValueError("Fusion sketch support body does not match the Cut target")
    FeatureId = ReadNativeRef(Sketch)
    Feature = SelectCursor(BulkData, Owners, FeatureId, KSketchFeature)
    Feature.Offset = 56
    if len(Feature.DataValue) != 425 or ReadNativeRef(Feature) != SketchId:
        raise ValueError("Fusion body supported sketch ownership disagrees")
    Feature.Offset = 191
    if Feature.ReadWord() != 12:
        raise ValueError("Unsupported Fusion face supported sketch dependencies")
    Dependencies = tuple(ReadNativeRef(Feature) for _ in range(12))
    if len(set(Dependencies)) != 12 or any(
        Identity not in Owners for Identity in Dependencies
    ):
        raise ValueError("Fusion sketch face support dependencies are unresolved")
    ProxyId, DescriptorId = Dependencies[2:4]
    Picks, Attributes = ReadSelectIds(BulkData, Owners, ProxyId, FeatureId, 1)
    if Picks != (DescriptorId,) or Attributes:
        raise ValueError("Fusion sketch support proxy and descriptor disagree")
    CheckInputProxy(BulkData, Owners, ProxyId, Picks, KSketchFaceMode)
    return FeatureId, ProxyId, DescriptorId
