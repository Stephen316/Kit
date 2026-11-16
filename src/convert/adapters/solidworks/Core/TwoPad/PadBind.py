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
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.Records.RecordProvenance import ProvenanceSpan


# each edge preserves the two directed endpoints used by the neutral loop
def PadEdgeKey(Entity: SketchEntity) -> tuple[tuple[float, float], tuple[float, float]]:
    Value = Entity.geometry
    if not isinstance(Value, LineGeometry) or Entity.construction:
        raise ValueError("Upper-pad perimeter member is not a profile line")
    First = (Value.start.x, Value.start.y)
    Second = (Value.end.x, Value.end.y)
    return First, Second


# the typed closed loop must identify exactly the already exposed neutral perimeter
def CheckPadLoop(SketchValue: Sketch, Profile: ProfileSketch, StreamName: str) -> None:
    Inline = InlineRead(Profile.Geometry, Profile.Coincidences, Profile.Members)
    TypedLines = BuildCutLoop(Inline, SketchValue.id, StreamName)
    RequireArch(
        len(SketchValue.closed_profile_entity_ids), 1, "one upper-pad perimeter"
    )
    (LoopValue,) = SketchValue.closed_profile_entity_ids
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    NeutralEdges = tuple(PadEdgeKey(Entities[Identity]) for Identity in LoopValue)
    TypedEdges = tuple(PadEdgeKey(Entity) for Entity in TypedLines)
    RequireArch(
        any(
            NeutralEdges == TypedEdges[Index:] + TypedEdges[:Index]
            for Index in range(len(TypedEdges))
        ),
        True,
        "upper-pad perimeter agrees with the typed directed loop",
    )


# unknown relation semantics remain a source span and two native line identities
def AttachPadPair(
    SketchValue: Sketch, PairValue: PadLinePair, StreamName: str
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
    return Replace(
        SketchValue,
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
