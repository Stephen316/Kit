# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from math import degrees as Degrees, tau as FullTurn

from convert.adapters.freecad.EditableExt import EditExtrude
from convert.adapters.freecad.EditableRev import EditRevolve
from convert.adapters.freecad.EditAxisRev.AxisProfile import ReadAxisProfile
from convert.adapters.freecad.EditBodyRev.BodyRevEdge import (
    ReadBodyPick,
    ReadSeedAxis,
    ReadSeedLine,
)
from convert.adapters.freecad.EditBodyRev.BodyRevModels import (
    CheckMembers,
    CheckBodyRecord,
)
from convert.adapters.freecad.EditBodyRev.BodyRevParams import (
    ReadSeedDepth,
    SplitBodyParams,
)
from convert.adapters.freecad.EditBodyRev.BodyRevScope import (
    CheckBodyScope,
    ReadBodyInputs,
)
from convert.adapters.freecad.EditExtRing import GetEditRing
from convert.adapters.freecad.EditExtSolid import BuildEditSolid
from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# both live controls share an exact source edge while each solid keeps its own geometry
@MakeDataClass(frozen=True, slots=True)
class BodyRevPlan:
    Extrude: EditExtrude
    Revolve: EditRevolve
    ExtrudeModel: BrepModel
    RevolveModel: BrepModel
    ExtrudeId: str
    RevolveId: str
    SourceBodyId: str
    ResultBodyId: str
    AxisEdgeId: str
    AxisLineId: str
    AxisStart: SpaceVector
    AxisEnd: SpaceVector
    AxisSense: int
    ProfilePairs: tuple[tuple[str, str], ...]
    SourceFrame: Transform
    ProfileFrame: Transform


# compare each independently rebuilt body and their complete original joined model
def CheckSavedPair(
    DocValue: CadDocument,
    FeatureValue: FeatureStep,
    Definition: AngularRevolve,
    SourcePlan: EditExtrude,
    ProfilePlan: EditRevolve,
    Interval: tuple[float, float],
) -> BodyRevPlan:
    Source, Profile = ReadBodyInputs(DocValue)
    _, Creator, _, _ = DocValue.feature_timeline
    SeedBody, RevBody = DocValue.bodies
    SourceFrame, ProfileFrame = (
        Source.PlaneValue.transform,
        Profile.PlaneValue.transform,
    )
    CheckMembers(DocValue, Source.PlaneValue.attributes["fusion.component_object_id"])
    LineRing = GetEditRing(Creator, Source.SketchValue)
    if LineRing is None or SourceFrame.z_axis != SourcePlan.Direction:
        raise ValueError("FreeCAD editable body axis Revolve source ring is unresolved")
    Pairs = ReadAxisProfile(FeatureValue, Profile.SketchValue)
    SeedGeom = BuildEditSolid(SeedBody.id, SourceFrame, LineRing, SourcePlan.DistanceMm)
    RevGeom = BuildRevGeom(
        RevBody.id,
        FeatureValue,
        Definition,
        Interval,
        Profile.SketchValue,
        ProfileFrame,
    )
    CheckBodyRecord(SeedBody, Creator, SeedGeom, "source_profile_extrude")
    CheckBodyRecord(RevBody, FeatureValue, RevGeom, "source_profile_revolve")
    SeedModel, RevModel = SeedGeom[0], RevGeom[0]
    if DocValue.brep != JoinRevModels((SeedModel, RevModel)):
        raise ValueError(
            "FreeCAD editable body axis Revolve saved joined geometry disagrees"
        )
    (PickValue,) = DocValue.selections
    EdgeId = ReadBodyPick(PickValue, FeatureValue, Definition, SeedBody, Creator)
    LineId, LineValue, RimStart, RimEnd = ReadSeedLine(
        EdgeId, SeedModel, Source.SketchValue, LineRing
    )
    Start, Finish, Sense = ReadSeedAxis(
        PickValue, Definition, LineValue, SourceFrame, RimStart, RimEnd
    )
    return BodyRevPlan(
        SourcePlan,
        ProfilePlan,
        SeedModel,
        RevModel,
        Creator.id,
        FeatureValue.id,
        SeedBody.id,
        RevBody.id,
        EdgeId,
        LineId,
        Start,
        Finish,
        Sense,
        Pairs,
        SourceFrame,
        ProfileFrame,
    )


# only literal simple linked creation features qualify as an editable native pair
def ReadBodyRev(DocValue: CadDocument, FeatureValue: FeatureStep) -> BodyRevPlan | None:
    Definition = FeatureValue.definition
    if not isinstance(Definition, AngularRevolve) or Definition.SideMode != "one_sided":
        return None
    try:
        CheckBodyScope(DocValue, FeatureValue)
        _, Creator, _, _ = DocValue.feature_timeline
        SourceDef = Creator.definition
        if (
            not isinstance(SourceDef, DistanceExtrude)
            or Creator.sketch_id is None
            or FeatureValue.sketch_id is None
        ):
            return None
        SourceParams, RevParams = SplitBodyParams(
            DocValue.parameters, Creator, FeatureValue
        )
        Depth = ReadSeedDepth(Creator, SourceDef, SourceParams)
        Along, Against = ReadRevAngles(FeatureValue, Definition, RevParams)
        Interval = GetAngleSpan(Along, Against, Definition.SideMode)
        if Interval[1] - Interval[0] > FullTurn:
            return None
        SourcePlan = EditExtrude(
            Creator.sketch_id,
            SourceDef.AlongParameterId,
            Depth,
            SourceDef.Direction,
            ProfileEditable=True,
            LineRing=True,
        )
        ProfilePlan = EditRevolve(
            FeatureValue.sketch_id,
            Definition.AxisOrigin,
            Definition.AxisDirection,
            Degrees(Along),
            Definition.AlongParameterId,
        )
        return CheckSavedPair(
            DocValue, FeatureValue, Definition, SourcePlan, ProfilePlan, Interval
        )
    except (AttributeError, IndexError, KeyError, OverflowError, TypeError, ValueError):
        return None
