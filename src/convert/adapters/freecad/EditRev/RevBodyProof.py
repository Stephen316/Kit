# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections.abc import Mapping

from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid
from convert.formats.Fusion.Topology.BodyCollection import KBodyCollection
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordTopology import TopologyCounts


# cached inventory must identify only the same reciprocal source body and component
def CheckRevInv(
    DocValue: CadDocument, BodyValue: DesignBody, Component: int, NativeId: int
) -> None:
    Inventory = DocValue.metadata.get("fusion.body_inventory")
    Members = Inventory.get("members") if isinstance(Inventory, Mapping) else None
    if (
        not isinstance(Members, tuple)
        or len(Members) != 1
        or Inventory.get("component_id") != Component
    ):
        raise ValueError("FreeCAD editable Revolve native body inventory is unresolved")
    (Member,) = Members
    if (
        not isinstance(Member, Mapping)
        or Member.get("object_id") != NativeId
        or Member.get("design_body_id") != BodyValue.id
        or Member.get("collection_id")
        != BodyValue.attributes.get("fusion.native_body_collection_id")
    ):
        raise ValueError("FreeCAD editable Revolve native body membership disagrees")


# native body ownership and complete rebuilt topology must agree before a feature goes live
def CheckRevBody(
    BodyValue: DesignBody,
    DocValue: CadDocument,
    FeatureValue: FeatureStep,
    Definition: AngularRevolve | PlaneRevolve,
    Interval: tuple[float, float],
    SketchValue: Sketch,
    PlaneValue: SupportPlane,
) -> None:
    Origin = BodyValue.provenance
    Attrs = BodyValue.attributes
    Component = PlaneValue.attributes.get("fusion.component_object_id")
    if (
        DocValue.brep is None
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or not Origin.spans
        or Origin.spans[0].record_kind != KBodyGuid
        or all(SpanValue.record_kind != KBodyCollection for SpanValue in Origin.spans)
        or BodyValue.id != f"fusion-derived-body-{FeatureValue.id}"
        or Attrs.get("fusion.geometry_source") != "source_profile_revolve"
        or type(Component) is not int
        or Component <= 0
        or Attrs.get("fusion.component_object_id") != Component
        or any(
            type(Attrs.get(Field)) is not int or Attrs[Field] <= 0
            for Field in (
                "fusion.native_body_anchor_id",
                "fusion.native_body_collection_id",
            )
        )
    ):
        raise ValueError(
            "FreeCAD editable Revolve saved result ownership is unresolved"
        )
    CheckRevInv(DocValue, BodyValue, Component, int(Origin.native_id))
    Model, Volume, AreaValue, Bounds = BuildRevGeom(
        BodyValue.id,
        FeatureValue,
        Definition,
        Interval,
        SketchValue,
        PlaneValue.transform,
    )
    Expected = TopologyCounts(
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
    if (
        len(Model.regions) != 1
        or DocValue.brep != Model
        or BodyValue.topology != Expected
    ):
        raise ValueError("FreeCAD editable Revolve saved result geometry disagrees")
