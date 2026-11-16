# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from struct import error as StructError

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Cut.CutOwners import FindCutOwner
from convert.adapters.solidworks.Core.Cut.FaceChart import PlaceCutFrame
from convert.adapters.solidworks.Core.Cut.FaceProjection import (
    AttachCutFrame,
    CheckCutPlane,
    FindCutBoss,
)
from convert.adapters.solidworks.Core.Cut.FaceSelection import (
    CutFaceSource,
    MakeCutFacePick,
)
from convert.adapters.solidworks.Core.TwoPad.PadBind import AttachPadPair, CheckPadLoop
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import (
    KPadListCount,
    PadHistory,
    ReadPadHistory,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.SupportPlane import SupportPlane


# the neutral projection must retain the verified authored blind dimensions and join order
def CheckPadDepth(StepValue: FeatureStep, Metres: float) -> None:
    Definition = StepValue.definition
    if not isinstance(Definition, ExtrudeFeature) or Definition.length is None:
        raise ValueError("The reached pad has no neutral blind depth")
    RequireArch(
        (
            StepValue.kind,
            StepValue.operation,
            StepValue.suppressed,
            Definition.end_condition,
            Definition.reversed,
            Definition.symmetric,
            Definition.length.value,
            Definition.length.unit,
        ),
        (
            FeatureKind.KExtrusion,
            BooleanOp.KJoin,
            False,
            ExtrudeEnd.KBlind,
            False,
            False,
            Metres * 1000,
            "mm",
        ),
        "neutral pad agrees with its authored blind join",
    )


# only the typed earlier positive cap can replace the provisional upper sketch plane
def BindPadDoc(
    Document: CadDocument, Proof: PadHistory, StreamName: str
) -> CadDocument:
    Profile = Proof.UpperProfile
    SketchValue, ProfileStep = FindCutOwner(Document, Profile.FeatureId)
    RequireArch(SketchValue.name, Profile.NameValue, "same upper-pad sketch name")
    CheckPadLoop(SketchValue, Profile, StreamName)
    BossId = Proof.BaseValue["native_feature_id"]
    BossStep = FindCutBoss(Document, ProfileStep, BossId)
    CheckPadDepth(BossStep, Proof.BaseEnd["depth_display"]["dimension"]["metres"])
    CheckCutPlane(Document, SketchValue, ProfileStep, BossStep)
    UpperId = f"sldprt:feature:{Proof.UpperValue['native_feature_id']}"
    (UpperStep,) = tuple(
        StepValue for StepValue in Document.feature_timeline if StepValue.id == UpperId
    )
    DepthValue = Proof.UpperValue["end_specification"]["depth_display"]
    if DepthValue is None:
        raise ValueError("The upper-pad join has no authored blind depth")
    CheckPadDepth(UpperStep, DepthValue["dimension"]["metres"])
    RequireArch(
        (
            UpperStep.name,
            UpperStep.sketch_id,
            BossStep.id in UpperStep.input_feature_ids,
            ProfileStep.order < UpperStep.order,
        ),
        (Proof.UpperValue["name"], SketchValue.id, True, True),
        "upper join consumes the reached profile and earlier boss",
    )
    Support = Proof.Support
    Frame = PlaceCutFrame(Support["face"]["plane"])
    Source = CutFaceSource(Support, StreamName, RoleName="pad-face")
    FacePick = MakeCutFacePick(
        BossStep, BossId, Profile.FeatureId, Support, Frame.origin, Source
    )
    PlaneId = f"sldprt:plane:{Profile.FeatureId}:face"
    RequireArch(
        any(Value.id == PlaneId for Value in Document.support_planes),
        False,
        "unique pad support plane",
    )
    RequireArch(
        any(Value.id == FacePick.id for Value in Document.selections),
        False,
        "unique pad support selection",
    )
    PlaneValue = SupportPlane(
        id=PlaneId,
        name=f"{SketchValue.name} face support",
        transform=Frame,
        support_selection_id=FacePick.id,
        provenance=Source,
    )
    Placed = AttachCutFrame(
        Document, SketchValue, ProfileStep, BossStep, PlaneValue, FacePick, None
    )
    return Replace(
        Placed,
        sketches=tuple(
            (
                AttachPadPair(Value, Proof.UpperPair, StreamName)
                if Value.id == SketchValue.id
                else Value
            )
            for Value in Placed.sketches
        ),
    )


# the short resolved list can refine only a structurally completed document
def ProjectPadDoc(
    Document: CadDocument, Archive: SldprtArchive, ConfigId: int | None
) -> CadDocument:
    if ConfigId != 0 or ContainerMo(Archive.streams) != KConfigGen:
        return Document
    StreamName = "Contents/Config-0-ResolvedFeatures"
    Resolved = Archive.get(StreamName)
    ConfigData = Archive.get("Contents/Config-0")
    if (
        Resolved is None
        or ConfigData is None
        or int.from_bytes(Resolved[4:6], "little") != KPadListCount
    ):
        return Document
    try:
        return BindPadDoc(Document, ReadPadHistory(ConfigData, Resolved), StreamName)
    except (IndexError, KeyError, StructError, ValueError):
        return Document
