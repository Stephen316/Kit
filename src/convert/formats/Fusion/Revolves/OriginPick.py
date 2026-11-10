# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import ReadOriginAxis
from convert.formats.Fusion.Topology.PickSupport import ReadPickSupport
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.VectorSpace import SpaceVector


# native origin membership makes the built in component axis independently selectable
def ReadOriginPick(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SelectId: int,
    AxisId: int,
    ComponentId: int,
    Descriptor: int,
    Terminal: int,
    SupportId: int,
) -> tuple[Selection, SpaceVector, SpaceVector]:
    ReadPickSupport(BulkData, Owners, SupportId, Descriptor, Descriptor)
    AxisName, AxisOrigin, Direction, ContainerId = ReadOriginAxis(
        BulkData, Owners, AxisId, ComponentId
    )
    SelectOrigin = ParamOrigin(Owners[SelectId])
    Evidence = SelectOrigin.spans + tuple(
        SpanValue
        for Identity in (Descriptor, Terminal, SupportId, AxisId, ContainerId)
        for SpanValue in ParamOrigin(Owners[Identity]).spans
    )
    SelectionValue = Selection(
        id=f"fusion-selection-{SelectId}-axis",
        name="axis",
        path=(),
        query=FreezeMapping({"kind": "component_origin_axis", "axis": AxisName}),
        provenance=Replace(SelectOrigin, spans=Evidence),
    )
    return SelectionValue, AxisOrigin, Direction
