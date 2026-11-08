# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections.abc import Mapping

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
    Members = Inventory.get("members") if isinstance(Inventory, Mapping) else None
    if (
        not isinstance(Members, tuple)
        or len(Members) != 2
        or Inventory.get("component_id") != Component
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve body inventory is unresolved"
        )
    for Member, BodyValue in zip(Members, DocValue.bodies, strict=True):
        Origin = BodyValue.provenance
        Attrs = BodyValue.attributes
        if (
            not isinstance(Member, Mapping)
            or Origin is None
            or type(Member.get("object_id")) is not int
            or Member["object_id"] <= 0
            or Origin.native_id != str(Member["object_id"])
            or Member.get("design_body_id") != BodyValue.id
            or Member.get("collection_id")
            != Attrs.get("fusion.native_body_collection_id")
            or Attrs.get("fusion.component_object_id") != Component
        ):
            raise ValueError(
                "FreeCAD editable body axis Revolve body membership disagrees"
            )
    if Members[0]["object_id"] == Members[1]["object_id"]:
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
            type(Attrs.get(Field)) is not int or Attrs[Field] <= 0
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
