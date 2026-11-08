# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Extrudes.BuildSolidStep import BuildSolidStep
from convert.formats.Fusion.Extrudes.ExtBodyLinks import LinkSolidBodies
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep


# component local geometry is grouped before assembly occurrences can apply placement
def BuildSolidSets(
    Document: CadDocument,
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Creators: tuple[FeatureStep, ...],
    Members: tuple[NativeBody, ...],
) -> dict[int, tuple[tuple[DesignBody, ...], BrepModel]]:
    Sketches = {SketchValue.id: SketchValue for SketchValue in Document.sketches}
    Frames = {FrameValue.id: FrameValue for FrameValue in Document.support_planes}
    Params = {Param.id: Param for Param in Document.parameters}
    Bodies: dict[int, list[DesignBody]] = {}
    Models: dict[int, list[BrepModel]] = {}
    Links = LinkSolidBodies(BulkData, Owners, Creators, Members)
    for StepValue in Creators:
        SketchValue = Sketches.get(StepValue.sketch_id or "")
        FrameValue = (
            None if SketchValue is None else Frames.get(SketchValue.support_plane_id)
        )
        if SketchValue is None or FrameValue is None:
            raise ValueError("Missing Fusion solid profile sketch frame")
        Member, AnchorId = Links[StepValue.id]
        BodyValue, Model = BuildSolidStep(
            Owners, StepValue, SketchValue, FrameValue, Params, Member, AnchorId
        )
        Bodies.setdefault(Member.ComponentId, []).append(BodyValue)
        Models.setdefault(Member.ComponentId, []).append(Model)
    return {
        ComponentId: (tuple(BodyList), JoinRevModels(tuple(Models[ComponentId])))
        for ComponentId, BodyList in Bodies.items()
    }
