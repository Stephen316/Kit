from convert.formats.Fusion.BodyInputs.ProxyInputCheck import CheckInputProxy
from convert.formats.Fusion.Extrudes.Plane.PlanePickSupport import KSketchFaceMode
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectIds, SelectCursor
from convert.formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf
from convert.formats.Fusion.Sketches.CenterDeps.ProjectionEntry import ReadProjEntry
from convert.formats.Fusion.Sketches.CenterDeps.ProjectionRefs import ProjectionRefs
from convert.formats.Fusion.Sketches.FaceSupport.FaceOwner import ReadFaceDeps

# the typed single output controller is separate from the automatic cap boundary controller
KProjController = "F1451EC8-11A4-4952-84ED-5AB7C13E2E83"


# independent proxy and output leaves must identify the same native source point
def ReadOriginProj(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchId: int, BodyId: int
) -> ProjectionRefs:
    FeatureId, DepsValue = ReadFaceDeps(BulkData, Owners, SketchId, BodyId)
    ProxyId, DescriptorId, ControllerId = DepsValue[5:8]
    Controller = SelectCursor(BulkData, Owners, ControllerId, KProjController)
    if len(Controller.DataValue) != 105 or Controller.TakeBytes(6) != b"\0\0\1\0\0\1":
        raise ValueError("Unsupported Fusion origin projection controller")
    EntryId = ReadNativeRef(Controller)
    Controller.Offset = 26
    if (
        Controller.ReadWord() != 3
        or ReadNativeRef(Controller) != FeatureId
        or ReadNativeRef(Controller) != ProxyId
    ):
        raise ValueError("Fusion origin projection controller and owner disagree")
    Controller.Offset = 94
    if ReadNativeRef(Controller) != FeatureId:
        raise ValueError("Fusion origin projection controller owner copy disagrees")
    Picks, Attributes = ReadSelectIds(BulkData, Owners, ProxyId, FeatureId, 1)
    if Picks != (DescriptorId,) or Attributes:
        raise ValueError("Fusion origin projection dependency and proxy disagree")
    CheckInputProxy(BulkData, Owners, ProxyId, Picks, KSketchFaceMode)
    SourceLeaf = ReadDescLeaf(BulkData, Owners, DescriptorId, FeatureId)
    OutputId, NamingId, OutputLeaf = ReadProjEntry(BulkData, Owners, EntryId)
    SourceId = ReadEntityLeaf(BulkData, Owners, SourceLeaf)
    if SourceLeaf == OutputLeaf or SourceId != ReadEntityLeaf(
        BulkData, Owners, OutputLeaf
    ):
        raise ValueError("Fusion projection source and output point name disagree")
    Records = (
        FeatureId,
        ControllerId,
        ProxyId,
        DescriptorId,
        EntryId,
        NamingId,
        SourceLeaf,
        OutputLeaf,
        SourceId,
    )
    return ProjectionRefs(OutputId, SourceId, Records)
