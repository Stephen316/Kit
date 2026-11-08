# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import PlaneRevPlan
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.EditProfile import CheckEditPlane
from convert.adapters.freecad.EditRead.PlaneRev.PlaneGraphLinks import (
    CheckDatumStep,
    CheckPlaneJson,
    CheckPlaneLink,
    CheckPlaneLinks,
    CheckStringRows,
    CheckTargetPick,
)
from convert.adapters.freecad.EditRead.PlaneRev.PlaneNodes import (
    PlaneNodes,
    ReadPlaneNodes,
)
from convert.adapters.freecad.EditRead.Revolve.RevGraph import (
    CheckRevScaf,
    ReadRevFiles,
)
from convert.adapters.freecad.EditRead.Revolve.RevGraphLinks import (
    CheckRevCarrier,
    CheckRevConfig,
    CheckRevDeps,
    CheckRevPick,
)
from convert.adapters.freecad.EditRead.Sketch.SketchDefaults import CheckExtensions
from convert.adapters.freecad.Native import NativeObject
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import KTransformIdentity


# resolved feature and cache identities precede interpretation of changed native controls
@MakeDataClass(frozen=True, slots=True)
class PlaneGraph:
    Feature: NativeObject
    Profile: NativeObject
    Sheet: NativeObject
    Targets: tuple[NativeObject, ...]
    ShapeEntry: str
    SketchEntry: str
    EmptyEntries: tuple[str, ...]


# original plane construction and sketch history must remain the only result dependencies
def CheckPlaneHist(
    Nodes: PlaneNodes, DocValue: CadDocument, PlanValue: PlaneRevPlan
) -> None:
    Timeline = DocValue.feature_timeline
    SketchNative, *Carriers, _ = Nodes.Timeline
    CheckRevCarrier(SketchNative, Timeline[0], Nodes.Profile.name)
    CheckStringRows(SketchNative, "ParameterIds", ())
    Steps = {
        Value.id: (Value, Native)
        for Value, Native in zip(Timeline[1:-1], Carriers, strict=True)
    }
    for Target in PlanValue.Targets:
        StepValue, Native = Steps[Target.StepId]
        CheckDatumStep(Native, StepValue, Nodes.Planes[Target.PlaneId].name)
    for Native in Nodes.Timeline[:-1]:
        CheckExtensions(Native)


# source plane and selection metadata remain reciprocal when native placement changes
def CheckPlanePicks(
    Nodes: PlaneNodes, DocValue: CadDocument, Definition: PlaneRevolve
) -> None:
    for PlaneValue in DocValue.support_planes:
        Native = Nodes.Planes[PlaneValue.id]
        CheckExtensions(Native)
        CheckPlaneJson(Native, "SourcePlaneJSON", PlaneValue)
    for PickValue in DocValue.selections:
        Native = Nodes.Picks[PickValue.id]
        if PickValue.id == Definition.AxisSelectionId:
            CheckExtensions(Native)
            CheckRevPick(Native, PickValue)
        else:
            CheckTargetPick(
                Native, PickValue, Nodes.Planes[PickValue.path[0].entity_id].name
            )


# exact ordered groups and cache owners exclude any second modeled shape
def ReadPlaneScaf(
    Objects: tuple[NativeObject, ...], Nodes: PlaneNodes, DocValue: CadDocument
) -> tuple[str, str, tuple[str, ...]]:
    Feature = Nodes.Timeline[-1]
    NativeBody = Nodes.BodyValue
    TimelineNames = tuple(Native.name for Native in Nodes.Timeline)
    Groups = {
        "SupportPlanes": tuple(Native.name for Native in Nodes.Planes.values()),
        "Sketches": (Nodes.Profile.name,),
        "Selections": tuple(Native.name for Native in Nodes.Picks.values()),
        "Configurations": (Nodes.Config.name,),
        "FeatureTimeline": TimelineNames,
        "Bodies": (NativeBody.name,),
        NativeBody.name: (Nodes.Profile.name, *TimelineNames),
    }
    Expected = {
        Nodes.Profile.name,
        Nodes.Sheet.name,
        Nodes.Config.name,
        *TimelineNames,
        *(Native.name for Native in Nodes.Planes.values()),
        *(Native.name for Native in Nodes.Picks.values()),
    }
    ShapeEntry, SketchEntry, EmptyEntries = ReadRevFiles(
        Objects, Feature, Nodes.Profile, Expected
    )
    ByName = {Native.name: Native for Native in Objects}
    CheckRevScaf(
        ByName,
        Feature,
        ShapeEntry,
        Groups,
        Expected,
    )
    CheckExtensions(ByName["KitMetadata"])
    CheckPlaneLink(NativeBody, "Tip", Feature.name)
    CheckEditFrame(NativeBody, "Placement", KTransformIdentity, Optional=True)
    CheckPlaneJson(NativeBody, "SourceBodyJSON", DocValue.bodies[0])
    CheckPlaneJson(NativeBody, "TopologyJSON", DocValue.bodies[0].topology)
    AllowedEmpty = {
        f"{Nodes.Profile.name}.InternalShape.brp",
        *(f"{Native.name}.Shape.brp" for Native in Nodes.Timeline[:-1]),
    }
    if set(EmptyEntries) - AllowedEmpty:
        raise ValueError("FreeCAD editable plane Revolve empty cache ownership changed")
    return ShapeEntry, SketchEntry, EmptyEntries


# every modeling object must still be tied to the original standalone feature graph
def ReadPlaneGraph(
    Objects: tuple[NativeObject, ...],
    DocValue: CadDocument,
    PlanValue: PlaneRevPlan,
    Definition: PlaneRevolve,
    SketchPlane: SupportPlane,
) -> PlaneGraph:
    Nodes = ReadPlaneNodes(Objects, DocValue)
    Feature = Nodes.Timeline[-1]
    CheckPlaneHist(Nodes, DocValue, PlanValue)
    CheckPlanePicks(Nodes, DocValue, Definition)
    CheckRevConfig(Nodes.Config)
    CheckExtensions(Nodes.Config)
    Support = Nodes.Planes[SketchPlane.id]
    CheckEditPlane(Nodes.Profile, Support, SketchPlane)
    CheckRevDeps(Support, ())
    CheckRevDeps(Nodes.Profile, (Support.name,))
    Targets = tuple(Nodes.Planes[Target.PlaneId] for Target in PlanValue.Targets)
    for Native in Targets:
        CheckRevDeps(Native, (Nodes.Sheet.name,))
    CheckPlaneLinks(
        Feature,
        DocValue.feature_timeline[-1],
        Nodes.Profile.name,
        tuple(Native.name for Native in Targets),
        tuple(
            Nodes.Picks[Identity].name
            for Identity in DocValue.feature_timeline[-1].selection_ids
        ),
    )
    ShapeEntry, SketchEntry, EmptyEntries = ReadPlaneScaf(Objects, Nodes, DocValue)
    return PlaneGraph(
        Feature,
        Nodes.Profile,
        Nodes.Sheet,
        Targets,
        ShapeEntry,
        SketchEntry,
        EmptyEntries,
    )
