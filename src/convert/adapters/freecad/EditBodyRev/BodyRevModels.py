from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.adapters.base.WriteValidate import IsObjectMap
from convert.formats.Fusion.Topology.BodyAnchor import KAnchorGuid, KBodyGuid
from convert.formats.Fusion.Topology.BodyCollection import KBodyCollection
from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.records.RecordTopology import TopologyCounts


# inventory evidence covers exactly the two saved bodies with reciprocal native ownership
def CheckMembers(DocValue: CadDocument, Component: int) -> None:
    Inventory = DocValue.metadata.get("fusion.body_inventory")
    if (
        not IsObjectMap(Inventory)
        or Inventory.get("component_id") != Component
        or not IsObjectTuple((Members := Inventory.get("members")))
        or len(Members) != 2
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve body inventory is unresolved"
        )
    Bodies = {BodyValue.id: BodyValue for BodyValue in DocValue.bodies}
    if len(DocValue.bodies) != 2 or len(Bodies) != 2:
        raise ValueError(
            "FreeCAD editable body axis Revolve body identity is ambiguous"
        )
    NativeIds: set[int] = set()
    for Member in Members:
        if not IsObjectMap(Member):
            raise ValueError(
                "FreeCAD editable body axis Revolve body membership disagrees"
            )
        BodyId = Member.get("design_body_id")
        NativeId = Member.get("object_id")
        BodyValue = Bodies.pop(BodyId, None) if isinstance(BodyId, str) else None
        if BodyValue is None or type(NativeId) is not int or NativeId <= 0:
            raise ValueError(
                "FreeCAD editable body axis Revolve body membership disagrees"
            )
        Origin = BodyValue.provenance
        Attrs = BodyValue.attributes
        if (
            Origin is None
            or Origin.native_id != str(NativeId)
            or Member.get("collection_id")
            != Attrs.get("fusion.native_body_collection_id")
            or Attrs.get("fusion.component_object_id") != Component
        ):
            raise ValueError(
                "FreeCAD editable body axis Revolve body membership disagrees"
            )
        NativeIds.add(NativeId)
    if len(NativeIds) != 2:
        raise ValueError(
            "FreeCAD editable body axis Revolve body identity is ambiguous"
        )


# native ownership and independently rebuilt geometry must agree for both bodies
def CheckBodyRecord(
    BodyValue: DesignBody,
    FeatureValue: FeatureStep,
    Geometry: tuple[BrepModel, float, float, BoundingBox],
    SourceKind: str,
) -> None:
    Origin = BodyValue.provenance
    Attrs = BodyValue.attributes
    if (
        Origin is None
        or Origin.adapter != "fusion.f3d"
        or tuple(Value.record_kind for Value in Origin.spans)
        != (KBodyGuid, KAnchorGuid, KBodyCollection)
        or BodyValue.id != f"fusion-derived-body-{FeatureValue.id}"
        or BodyValue.final_feature_id != FeatureValue.id
        or Attrs.get("fusion.geometry_source") != SourceKind
        or any(
            type(NativeId := Attrs.get(Field)) is not int or NativeId <= 0
            for Field in (
                "fusion.native_body_anchor_id",
                "fusion.native_body_collection_id",
            )
        )
    ):
        raise ValueError("FreeCAD editable body axis Revolve body provenance disagrees")
    Model = Geometry[0]
    if len(Model.regions) != 1 or BodyValue.topology != GetBodyTopology(Geometry):
        raise ValueError(
            "FreeCAD editable body axis Revolve saved body geometry disagrees"
        )


# both qualification and saved edit application compare identical analytic body measures
def GetBodyTopology(
    Geometry: tuple[BrepModel, float, float, BoundingBox],
) -> TopologyCounts:
    Model, Volume, AreaValue, Bounds = Geometry
    return TopologyCounts(
        solid_count=len(Model.regions),
        shell_count=len(Model.shells),
        face_count=len(Model.faces),
        edge_count=len(Model.edges),
        vertex_count=len(Model.vertices),
        volume=Volume,
        surface_area=AreaValue,
        bounding_box=Bounds,
        valid=True,
    )
