# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Cut.CutLoop import BuildCutLoop
from convert.adapters.solidworks.Resolved.ProfileSketch import ProfileSketch
from convert.adapters.solidworks.Resolved.TwoPad.PadProfile import PadLinePair
from convert.adapters.solidworks.Sketch.InlineSketch import InlineRead
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.Records.RecordProvenance import ProvenanceSpan


# each edge preserves the two directed endpoints used by the neutral loop
def PadEdgeKey(Entity: SketchEntity) -> tuple[tuple[float, float], tuple[float, float]]:
    Value = Entity.geometry
    if not isinstance(Value, LineGeometry) or Entity.construction:
        raise ValueError("Upper-pad perimeter member is not a profile line")
    First = (Value.start.x, Value.start.y)
    Second = (Value.end.x, Value.end.y)
    return First, Second


# the directed perimeter proves correspondence between native handles and neutral edges
def MapPadLoop(
    SketchValue: Sketch, Profile: ProfileSketch, StreamName: str
) -> dict[int, str]:
    Inline = InlineRead(Profile.Geometry, Profile.Coincidences, Profile.Members)
    TypedLines = BuildCutLoop(Inline, SketchValue.id, StreamName)
    RequireArch(
        len(SketchValue.closed_profile_entity_ids), 1, "one upper-pad perimeter"
    )
    (LoopValue,) = SketchValue.closed_profile_entity_ids
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    NeutralEdges = tuple(PadEdgeKey(Entities[Identity]) for Identity in LoopValue)
    TypedEdges = tuple(PadEdgeKey(Entity) for Entity in TypedLines)
    Rotations = tuple(
        Index
        for Index in range(len(TypedEdges))
        if NeutralEdges == TypedEdges[Index:] + TypedEdges[:Index]
    )
    RequireArch(len(Rotations), 1, "unique upper-pad directed perimeter correspondence")
    (Start,) = Rotations
    Ordered = TypedLines[Start:] + TypedLines[:Start]
    Bindings: dict[int, str] = {}
    for EntityId, TypedLine in zip(LoopValue, Ordered, strict=True):
        NativeId = TypedLine.attributes["native_segment_id"]
        if type(NativeId) is not int:
            raise ValueError("Upper-pad line has no typed native segment identity")
        Bindings[NativeId] = EntityId
    return Bindings


# the licensed equal length law keeps its compact owner evidence on the projected relation
def AttachPadPair(
    SketchValue: Sketch,
    PairValue: PadLinePair,
    StreamName: str,
    Bindings: dict[int, str],
) -> Sketch:
    SpanValue = ProvenanceSpan(
        StreamName,
        PairValue.Start,
        PairValue.StopValue - PairValue.Start,
        "native-line-relation",
    )
    Source = SketchValue.provenance
    if Source is None:
        raise ValueError("Upper-pad sketch has no native provenance")
    Relation = SketchRelation(
        f"{SketchValue.id}:native-line-relation:{PairValue.Start}",
        ConstraintKind.KEqual.value,
        tuple(ConstraintRef(Bindings[LineId]) for LineId in PairValue.Lines),
        provenance=Replace(Source, spans=(SpanValue,)),
    )
    return Replace(
        SketchValue,
        constraints=(*SketchValue.constraints, Relation),
        provenance=Replace(Source, spans=(*Source.spans, SpanValue)),
        attributes=FreezeMapping(
            {
                **SketchValue.attributes,
                "solidworks.native_line_relation": FreezeMapping(
                    {
                        "code": PairValue.CodeValue,
                        "handles": PairValue.Handles,
                        "line_ids": PairValue.Lines,
                    }
                ),
            }
        ),
    )
