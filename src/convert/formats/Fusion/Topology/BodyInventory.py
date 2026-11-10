# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.ComponentRead import KComponentBase
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyComponentLink import ReadCurrentLink
from convert.formats.Fusion.Topology.BodyName import ReadBodyName
from convert.formats.Fusion.Topology.CurrentBodyCollection import ReadCurrentList
from convert.formats.Fusion.Topology.NativeBody import NativeBody


# reuse typed indices and isolate unsupported saved memberships to their owning component
def ReadNativeList(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], ComponentIds: frozenset[int]
) -> tuple[dict[int, tuple[NativeBody, ...]], dict[int, str]]:
    Owners, Bases = IndexBodyOwners(Spans, len(BulkData), ComponentIds)
    Inventory: dict[int, tuple[NativeBody, ...]] = {}
    Issues: dict[int, str] = {}
    for ComponentId in sorted(ComponentIds):
        try:
            ComponentBases = Bases.get(ComponentId, ())
            if len(ComponentBases) != 1:
                raise ValueError(
                    "Missing or ambiguous Fusion body component continuation"
                )
            CollectionId = ReadCurrentLink(
                BulkData, Owners, ComponentBases[0], ComponentId
            )
            BodyIds = ReadCurrentList(BulkData, Owners, CollectionId, ComponentId)
            Bodies: list[NativeBody] = []
            for BodyId in BodyIds:
                try:
                    NameText, HelperId = ReadBodyName(
                        BulkData, Owners, BodyId, CollectionId
                    )
                except ValueError:
                    NameText, HelperId = "", None
                Bodies.append(
                    NativeBody(BodyId, ComponentId, CollectionId, NameText, HelperId)
                )
            Inventory[ComponentId] = tuple(Bodies)
        except ValueError as Error:
            Issues[ComponentId] = str(Error)
    return Inventory, Issues


# duplicate and malformed records cannot contribute body ownership claims
def IndexBodyOwners(
    Spans: tuple[RecordSpan, ...],
    ByteCount: int,
    ComponentIds: frozenset[int],
) -> tuple[dict[int, RecordSpan], dict[int, list[RecordSpan]]]:
    Owners: dict[int, RecordSpan] = {}
    UnusableIds: set[int] = set()
    Bases: dict[int, list[RecordSpan]] = {}
    for SpanValue in Spans:
        Identity = SpanValue.ObjectId
        if SpanValue.IsPrimary:
            if (
                Identity in Owners
                or not 0 <= SpanValue.PayloadOffset <= SpanValue.EndOffset - 4
                or SpanValue.EndOffset > ByteCount
            ):
                UnusableIds.add(Identity)
            else:
                Owners[Identity] = SpanValue
        elif Identity in ComponentIds and SpanValue.ClassGuid == KComponentBase:
            Bases.setdefault(Identity, []).append(SpanValue)
    for Identity in UnusableIds:
        _ = Owners.pop(Identity, None)
    return Owners, Bases


# component body readers share one entry point for ordered native membership and label evidence
ReadBodyInventory = ReadNativeList
