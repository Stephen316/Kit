# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginPick import ReadOriginPick
from convert.formats.Fusion.Revolves.SketchAxis import ReadSketchAxis
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import (
    KSelectDesc,
    KSelectLeaf,
    ReadEntityLeaf,
    ReadSelectLeaf,
)
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorSpace import SpaceVector


# angular sweeps need an editable axis and its directed geometry in the profile component
def ResolveAngleAxis(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Picks: tuple[Selection, ...],
    Sketches: dict[str, Sketch],
    Frames: dict[str, SupportPlane],
    ProfileFrame: SupportPlane,
) -> tuple[Selection, SpaceVector, SpaceVector]:
    Origin = StepValue.provenance
    ComponentId = ProfileFrame.attributes.get("fusion.component_object_id")
    SelectId = StepValue.attributes.get("fusion.revolve.axis_selection_id")
    AxisId = StepValue.attributes.get("fusion.revolve.axis_object_id")
    if Origin is None or type(ComponentId) is not int or type(SelectId) is not int:
        raise ValueError("Missing Fusion angular Revolve axis owner or selection")
    if type(AxisId) is not int:
        raise ValueError("Fusion angular Revolve needs an origin axis or a sketch line")
    Descriptor, Terminal = ReadSelectLeaf(
        BulkData, Owners, SelectId, int(Origin.native_id)
    )
    DescCursor = SelectCursor(BulkData, Owners, Descriptor, KSelectDesc)
    DescCursor.Offset = 240
    SupportId = ReadNativeRef(DescCursor)
    Leaf = Owners.get(Terminal)
    if Leaf is not None and Leaf.ClassGuid == KSelectLeaf:
        if ReadEntityLeaf(BulkData, Owners, Terminal) != AxisId:
            raise ValueError("Fusion angular Revolve origin axis selection disagrees")
        return ReadOriginPick(
            BulkData,
            Owners,
            SelectId,
            AxisId,
            ComponentId,
            Descriptor,
            Terminal,
            SupportId,
        )
    PickId = f"fusion-selection-{SelectId}-axis"
    Matches = tuple(Pick for Pick in Picks if Pick.id == PickId)
    if len(Matches) != 1 or PickId not in StepValue.selection_ids:
        raise ValueError("Missing or ambiguous Fusion Revolve sketch axis selection")
    PickValue = Matches[0]
    if PickValue.provenance is None or PickValue.provenance.native_id != str(SelectId):
        raise ValueError("Fusion Revolve sketch axis selection provenance disagrees")
    AxisOrigin, Direction = ReadSketchAxis(
        BulkData,
        Owners,
        PickValue,
        Sketches,
        Frames,
        ComponentId,
        AxisId,
        Descriptor,
        Terminal,
        SupportId,
    )
    return PickValue, AxisOrigin, Direction
