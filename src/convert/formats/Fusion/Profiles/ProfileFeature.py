# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.Profiles.LineRing import OrderLineRing
from convert.formats.Fusion.Profiles.ProfileLoop import ReadProfileLoop
from convert.formats.Fusion.Profiles.ProfileRef import KLoopGuid, ReadProfileRef
from convert.formats.Fusion.Profiles.SemiRing import OrderSemiRing
from convert.formats.Fusion.Profiles.TrimSourceGuard import CheckTrimInputs
from convert.formats.Fusion.Profiles.Trimmed.TrimProfile import ReadTrimProfile
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch


# projected feature inputs retain proof of their original profile membership
def AttachProfile(
    BulkData: bytes,
    StepValue: FeatureStep,
    Descriptor: RecordSpan,
    Owners: dict[int, RecordSpan],
    Sources: dict[int, tuple[Sketch, FeatureStep]],
) -> tuple[FeatureStep, Sketch, tuple[str, ...]]:
    SketchId, LoopId = ReadProfileRef(
        BulkData[Descriptor.PayloadOffset + 4 : Descriptor.EndOffset]
    )
    Source = Sources.get(SketchId)
    LoopSpan = Owners.get(LoopId)
    if Source is None or LoopSpan is None or LoopSpan.ClassGuid != KLoopGuid:
        raise ValueError("Missing typed Fusion profile loop or projected sketch")
    SketchValue, SketchStep = Source
    if SketchStep.order >= StepValue.order:
        raise ValueError("Fusion profile sketch does not precede its feature")
    LoopData = BulkData[LoopSpan.PayloadOffset + 4 : LoopSpan.EndOffset]
    try:
        Members, Directions = ReadProfileLoop(
            LoopData, Descriptor.ObjectId, SketchValue
        )
        Closed = OrderSemiRing(Members) if len(Members) == 2 else OrderLineRing(Members)
        Profile = {
            "fusion.profile_entity_ids": Closed,
            "fusion.profile_native_members": tuple(Entity.id for Entity in Members),
            "fusion.profile_native_directions": Directions,
        }
    except ValueError as WholeError:
        if StepValue.kind != FeatureKind.KExtrusion:
            raise
        try:
            Portions = ReadTrimProfile(LoopData, Descriptor.ObjectId, SketchValue)
        except ValueError as TrimError:
            raise WholeError from TrimError
        CheckTrimInputs(BulkData, Owners, SketchId, SketchValue)
        Closed = ()
        Profile = {
            "fusion.profile_portions": tuple(
                (Portion.EntityId, Portion.Lower, Portion.Upper, Portion.Selector)
                for Portion in Portions
            )
        }
    Origin = StepValue.provenance
    if Origin is None:
        raise ValueError("Missing Fusion profile feature provenance")
    return (
        Replace(
            StepValue,
            sketch_id=SketchValue.id,
            input_feature_ids=StepValue.input_feature_ids + (SketchStep.id,),
            provenance=Replace(
                Origin,
                spans=Origin.spans
                + RecordOrigin(Descriptor).spans
                + RecordOrigin(LoopSpan).spans,
            ),
            attributes=FreezeMapping(
                {
                    **StepValue.attributes,
                    "fusion.profile_descriptor_id": Descriptor.ObjectId,
                    **Profile,
                }
            ),
        ),
        SketchValue,
        Closed,
    )
