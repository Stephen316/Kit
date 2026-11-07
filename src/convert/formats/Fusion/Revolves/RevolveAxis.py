# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolveEdge import ResolveRevEdge
from convert.formats.Fusion.Revolves.RevolvePick import RevolvePick
from convert.formats.Fusion.SelectionProxy import ReadSelectDesc
from convert.formats.Fusion.SelectionRef import (
    KSelectLeaf,
    ReadEntityLeaf,
    ReadDescLeaf,
)
from convert.formats.Fusion.Sketches.SketchPick import FindSketchCurve, ReadSketchPick
from convert.formats.Fusion.Topology.PickDescriptor import KTopoSelect
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Selection import SelectPathElem
from interchange.geometry.models.Sketch import Sketch

# construction axes have their own primary class even without neutral axis geometry
KAxisObject = "19031004-3AB6-4D13-ABBF-C51EE214688D"


# axes dispatch by descriptor class before resolving construction or topology sources
def ResolveRevAxis(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SelectId: int,
    FeatureId: int,
    FeatureOrder: int,
    SketchLinks: dict[int, tuple[Sketch, FeatureStep]],
    FeatureLinks: dict[int, FeatureStep],
) -> RevolvePick:
    Descriptor = ReadSelectDesc(BulkData, Owners, SelectId, FeatureId)
    SpanValue = Owners.get(Descriptor)
    if SpanValue is not None and SpanValue.ClassGuid == KTopoSelect:
        return ResolveRevEdge(
            BulkData, Owners, Descriptor, FeatureId, FeatureOrder, FeatureLinks
        )
    Terminal = ReadDescLeaf(BulkData, Owners, Descriptor, FeatureId)
    Leaf = Owners.get(Terminal)
    if Leaf is not None and Leaf.ClassGuid == KSelectLeaf:
        EntityId = ReadEntityLeaf(BulkData, Owners, Terminal)
        Source = Owners.get(EntityId)
        if Source is None or Source.ClassGuid != KAxisObject:
            raise ValueError("Unsupported Fusion Revolve construction axis")
        return RevolvePick(EntityId, Descriptor, Terminal)
    SketchId, TagValue = ReadSketchPick(BulkData, Owners, Terminal)
    SourceLink = SketchLinks.get(SketchId)
    if SourceLink is None or SourceLink[1].order >= FeatureOrder:
        raise ValueError("Fusion Revolve axis sketch is outside prior history")
    SketchValue, SketchStep = SourceLink
    Entity = FindSketchCurve(SketchValue, TagValue)
    Geometry = Entity.geometry
    if (
        not isinstance(Geometry, LineGeometry)
        or Geometry.start == Geometry.end
        or Entity.provenance is None
    ):
        raise ValueError("Fusion Revolve axis selection requires a directed line")
    return RevolvePick(
        int(Entity.provenance.native_id),
        Descriptor,
        Terminal,
        (
            SelectPathElem("sketch", SketchValue.id),
            SelectPathElem("sketch_entity", Entity.id),
        ),
        SketchStep.id,
    )
