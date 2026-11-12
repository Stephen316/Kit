from collections.abc import Mapping
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditAxisRev.AxisReadSketch import ReadAxisSketch
from convert.adapters.freecad.EditBodyRev.ApplyBodyRevEdit import ApplyBodyRev
from convert.adapters.freecad.EditBodyRev.BodyReadCache import (
    CheckBodyCaches,
    ReadBodyCaches,
)
from convert.adapters.freecad.EditBodyRev.BodyReadCells import ReadBodyCells
from convert.adapters.freecad.EditBodyRev.BodyReadFrames import ReadBodyFrame
from convert.adapters.freecad.EditBodyRev.BodyReadGraph import ReadBodyGraph
from convert.adapters.freecad.EditBodyRev.BodyReadLinks import (
    CheckBodyExprs,
    CheckBodyLinks,
    CheckBodyPose,
)
from convert.adapters.freecad.EditBodyRev.BodyReadMap import ReadRimShadow
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan, ReadBodyRev
from convert.adapters.freecad.EditBodyRev.PrismOrder import ReadPrismOrder
from convert.adapters.freecad.EditRead.EditExtrusion import ReadEditDepth
from interchange.document.models.DocumentModel import CadDocument


# the saved compound history is accepted only when native controls and both body caches agree
def ReconcileBody(
    DocValue: CadDocument,
    Manifest: Mapping[str, object],
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    PlanValue: BodyRevPlan,
) -> CadDocument:
    Graph = ReadBodyGraph(RootValue, Manifest, DocValue, PlanValue)
    Caches = ReadBodyCaches(Members, Graph)
    Sketches = {Value.id: Value for Value in DocValue.sketches}
    Planes = {Value.id: Value for Value in DocValue.support_planes}
    Source, Profile = (
        Sketches[PlanValue.Extrude.SketchId],
        Sketches[PlanValue.Revolve.SketchId],
    )
    SourceFrame = ReadBodyFrame(
        tuple(Graph.Objects.values()), Graph.Source, Planes[Source.support_plane_id]
    )
    ProfileFrame = ReadBodyFrame(
        tuple(Graph.Objects.values()), Graph.Profile, Planes[Profile.support_plane_id]
    )
    Depth, Along, DepthRef = ReadBodyCells(
        Graph.Sheet,
        DocValue.parameters,
        PlanValue,
        ReadEditDepth(Graph.Seed, SourceFrame.z_axis),
    )
    CheckBodyExprs(Graph, PlanValue, DepthRef)
    EditedSource = ReadAxisSketch(
        Graph.Source, Graph.Template[Graph.Source.name], Source
    )
    EditedProfile = ReadAxisSketch(
        Graph.Profile, Graph.Template[Graph.Profile.name], Profile
    )
    Rebuilt = ApplyBodyRev(
        DocValue,
        PlanValue,
        EditedSource,
        EditedProfile,
        SourceFrame,
        ProfileFrame,
        Depth,
        Along,
    )
    if Caches.IsSeed and Rebuilt is not DocValue:
        raise ValueError(
            "FreeCAD editable body axis edits are missing their saved sketch caches"
        )
    Current = (
        PlanValue
        if Rebuilt is DocValue
        else ReadBodyRev(Rebuilt, Rebuilt.feature_timeline[-1])
    )
    if Current is None:
        raise ValueError("FreeCAD editable body axis edits no longer qualify")
    SolvedSource = next(Value for Value in Rebuilt.sketches if Value.id == Source.id)
    Order = ReadPrismOrder(
        Current.ExtrudeModel,
        SolvedSource,
        Current.SourceFrame,
        Current.AxisEdgeId,
        Current.AxisLineId,
        Current.Extrude.DistanceMm,
    )
    Shadow = ""
    if not Caches.IsSeed:
        GeoId = next(
            Index
            for Index, Entity in enumerate(Source.entities, 1)
            if Entity.id == PlanValue.AxisLineId
        )
        Shadow = ReadRimShadow(
            Archive,
            Members,
            Graph.Seed,
            int(Order.EdgeName.removeprefix("Edge")),
            GeoId,
            len(Source.closed_profile_entity_ids[0]),
        )
    CheckBodyLinks(Graph, Order.EdgeName, Shadow)
    CheckBodyPose(Graph, Order, Current, Along[0], Caches.IsSeed)
    CheckBodyCaches(Archive, Members, Caches, Source, Profile, Rebuilt, Current, Order)
    return Rebuilt
