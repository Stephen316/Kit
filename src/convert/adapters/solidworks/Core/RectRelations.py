from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.RectBindings import (
    KPointToleranceMm,
    RectBindings,
)
from convert.adapters.solidworks.Core.RectOrigin import RectOrigin
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry
from convert.adapters.solidworks.Sketch.MemberSpans import MemberSpan
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchRelation


# an axis rule keeps its public identity while the archived handle supplies the line target
def ProjectAxes(
    Neutral: Sketch, Geometry: SketchGeometry, Binding: RectBindings, StreamName: str
) -> tuple[SketchRelation, ...]:
    Targets = {EdgeValue.Source["native_id"]: EdgeValue for EdgeValue in Binding.Edges}
    Saved = {
        Targets[RowValue["segment_native_id"]].Entity.id: RowValue
        for RowValue in Geometry["member_relations"]
    }
    RequireArch(
        (len(Saved), len(Geometry["member_relations"])),
        (4, 4),
        "one saved axis relation per perimeter edge",
    )
    Replacements: dict[str, SketchRelation] = {}
    for RuleValue in Neutral.constraints:
        if RuleValue.kind not in ("horizontal", "vertical"):
            continue
        RequireArch(len(RuleValue.references), 1, "one line in neutral axis relation")
        (Reference,) = RuleValue.references
        RequireArch(Reference.point, "", "axis relation targets an entire line")
        RequireArch(
            Reference.entity_id not in Replacements,
            True,
            "unique neutral axis rule per edge",
        )
        RowValue = Saved[Reference.entity_id]
        Bound = Targets[RowValue["segment_native_id"]]
        FirstSlot, EndSlot = Bound.Slots
        AxisIndex = 1 if RowValue["kind"] == "horizontal" else 0
        RequireArch(
            abs(
                Binding.Points[FirstSlot][AxisIndex]
                - Binding.Points[EndSlot][AxisIndex]
            )
            <= KPointToleranceMm,
            True,
            "saved axis matches its local line",
        )
        Replacements[Reference.entity_id] = Replace(
            RuleValue,
            kind=RowValue["kind"],
            provenance=RectSource(
                str(RowValue["line_handle_object"]),
                StreamName,
                MemberSpan(RowValue["start"], RowValue["end"]),
                "sketch-axis-relation",
            ),
            attributes=FreezeMapping(
                {
                    **RuleValue.attributes,
                    "native_code": RowValue["type_code"],
                    "native_segment_id": RowValue["segment_native_id"],
                    "native_line_handle": RowValue["line_handle_object"],
                }
            ),
        )
    RequireArch(
        set(Replacements),
        set(Saved),
        "saved axis rules cover the established rectangle constraints",
    )
    Substitutes = {RuleValue.id: RuleValue for RuleValue in Replacements.values()}
    return tuple(
        Substitutes.get(RuleValue.id, RuleValue) for RuleValue in Neutral.constraints
    )


# the saved coincidence must preserve its operand order and the existing closed edge endpoint
def ProjectOrigin(
    Binding: RectBindings, Origin: RectOrigin, FeatureId: int, StreamName: str
) -> SketchRelation:
    Corners = [
        EdgeValue.Entity.id
        for EdgeValue in Binding.Edges
        if EdgeValue.Slots[0] == Origin.Vertex
    ]
    RequireArch(len(Corners), 1, "unique neutral endpoint for the archived corner")
    (Corner,) = Corners
    ProxySlot = Origin.Proxy["local_id"][0]
    Relation = Origin.Relation
    References = tuple(
        (
            ConstraintRef(Binding.PointEntities[ProxySlot].id)
            if PointId == Origin.Proxy["local_id"]
            else ConstraintRef(Corner, "start")
        )
        for PointId in Relation["point_native_ids"]
    )
    return SketchRelation(
        f"sldprt:constraint:{FeatureId}:native-relation:{Relation['offset']}",
        "coincident",
        References,
        provenance=RectSource(
            str(Relation["offset"]),
            StreamName,
            MemberSpan(Relation["offset"], Relation["end"]),
            "sketch-origin-coincidence",
        ),
        attributes=FreezeMapping(
            {
                "native_code": Relation["type_code"],
                "native_point_ids": tuple(Relation["point_native_ids"]),
                "native_point_handles": tuple(Relation["point_handle_objects"]),
                "native_origin_feature_id": Origin.Proxy["feature_id"],
            }
        ),
    )
