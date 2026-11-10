# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.Assembly.AssemblyModel import NativeAssembly
from convert.formats.Fusion.Assembly.ComponentRead import KComponentBase
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import AssemblyData
from interchange.records.RecordProvenance import Provenance


# component display labels and placement membership come from a separate base record
def ComponentOrigin(Primary: RecordSpan, BaseValue: RecordSpan) -> Provenance:
    Origin = ParamOrigin(Primary)
    return Replace(Origin, spans=Origin.spans + ParamOrigin(BaseValue).spans)


# local definitions and occurrences retain native identity and use neutral length units
def ProjectAssembly(
    Assembly: NativeAssembly,
    Spans: tuple[RecordSpan, ...],
    Histories: dict[int, HistoryPart],
) -> AssemblyData:
    Primary = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    BaseSpans = {
        SpanValue.ObjectId: SpanValue
        for SpanValue in Spans
        if SpanValue.ClassGuid == KComponentBase
    }
    Owners = {Occurrence.OwnerId for Occurrence in Assembly.Occurrences}
    Definitions = tuple(
        ComponentDef(
            id=f"fusion-component-{Component.ObjectId}",
            name=Component.Name,
            kind=(
                ComponentKind.KAssembly
                if Component.ObjectId in Owners
                else ComponentKind.KPart
            ),
            source_format_id="fusion.f3d",
            provenance=ComponentOrigin(
                Primary[Component.ObjectId], BaseSpans[Component.ObjectId]
            ),
            attributes=FreezeMapping(
                {
                    "fusion.native_guid": Component.NativeGuid,
                    "fusion.history_id": Histories[Component.ObjectId].HistoryId,
                }
            ),
        )
        for Component in Assembly.Components
    )
    Instances = tuple(
        ComponentInst(
            id=f"fusion-occurrence-{Occurrence.ObjectId}",
            name=Occurrence.Name,
            definition_id=f"fusion-component-{Occurrence.ComponentId}",
            owner_definition_id=f"fusion-component-{Occurrence.OwnerId}",
            transform=TransformMatrix(
                values=tuple(
                    Value * 10.0 if Index in (3, 7, 11) else Value
                    for Index, Value in enumerate(Occurrence.Transform)
                )
            ),
            order=Occurrence.Order,
            provenance=ParamOrigin(Primary[Occurrence.ObjectId]),
            attributes=FreezeMapping(
                {
                    "fusion.instance_number": Occurrence.InstanceNumber,
                    "fusion.native_guid": Occurrence.NativeGuid,
                }
            ),
        )
        for Occurrence in Assembly.Occurrences
    )
    return AssemblyData(
        root_definition_id=f"fusion-component-{Assembly.RootComponentId}",
        definitions=Definitions,
        instances=Instances,
    )
