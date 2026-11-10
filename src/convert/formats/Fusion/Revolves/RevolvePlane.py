# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.NativePlane import KPlaneObject
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolvePick import RevolvePick
from convert.formats.Fusion.SelectionRef import ReadEntityRef
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import SelectPathElem
from interchange.geometry.models.SupportPlane import SupportPlane


# a target plane selection resolves only against a preceding projected support frame
def ResolveRevPlane(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SelectId: int,
    FeatureId: int,
    FeatureOrder: int,
    PlaneLinks: dict[int, tuple[SupportPlane, FeatureStep]],
) -> RevolvePick:
    Descriptor, Terminal, EntityId = ReadEntityRef(
        BulkData, Owners, SelectId, FeatureId
    )
    Source = Owners.get(EntityId)
    PlaneLink = PlaneLinks.get(EntityId)
    if Source is None or Source.ClassGuid != KPlaneObject:
        raise ValueError("Unsupported Fusion Revolve construction plane")
    if PlaneLink is None or PlaneLink[1].order >= FeatureOrder:
        raise ValueError("Fusion Revolve target plane is outside prior history")
    PlaneValue, PlaneStep = PlaneLink
    return RevolvePick(
        EntityId,
        Descriptor,
        Terminal,
        (SelectPathElem("support_plane", PlaneValue.id),),
        PlaneStep.id,
    )
