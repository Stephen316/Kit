from convert.formats.Fusion.BodyInputs.ProxyInputCheck import CheckInputProxy
from convert.formats.Fusion.Extrudes.Plane.PlanePickSupport import KSketchFaceMode
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectIds
from convert.formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf
from convert.formats.Fusion.Sketches.CenterDeps.ProjectionEntry import ReadProjEntry
from convert.formats.Fusion.Sketches.CenterDeps.ProjectionRefs import ProjectionRefs
from convert.formats.Fusion.Sketches.FaceSupport.FaceOwner import ReadFaceDeps
from convert.formats.Fusion.Sketches.Projections.ProjController import ReadProjCtrl


# independent proxy and output leaves must identify the same native source point
def ReadOriginProj(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchId: int, BodyId: int
) -> ProjectionRefs:
    FeatureId, DepsValue = ReadFaceDeps(BulkData, Owners, SketchId, BodyId)
    ProxyId, DescriptorId, ControllerId = DepsValue[5:8]
    EntryId = ReadProjCtrl(BulkData, Owners, ControllerId, FeatureId, ProxyId, 3)
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
