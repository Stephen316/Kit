from dataclasses import replace as Replace
from math import tau as FullTurn

from convert.adapters.freecad.EditBodyRev.BodyAxisEdit import (
    BodyAxisEdit,
    BodyAxisVector,
    ReadEditedAxis,
    StoreAxisEdit,
)
from convert.adapters.freecad.EditBodyRev.BodyRevEdge import FindSeedEdge
from convert.adapters.freecad.EditBodyRev.BodyRevModels import GetBodyTopology
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan
from convert.adapters.freecad.EditExtRing import GetEditRing
from convert.adapters.freecad.EditExtSolid import BuildEditSolid
from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.formats.Fusion.Revolves.ProfileMeridian import CalcMeridian
from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Selection import SelectPathElem
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the occupied meridian controls the effective sweep even when the linked edge moves sides
def ReadNewAxis(
    FeatureValue: FeatureStep,
    Definition: AngularRevolve,
    Profile: Sketch,
    Frame: Transform,
    Start: SpaceVector,
    Finish: SpaceVector,
) -> AngularRevolve:
    Lines = ReadRevProfile(FeatureValue, Profile)
    if not isinstance(Lines, tuple):
        raise ValueError("FreeCAD editable body axis Revolve requires a line profile")
    Direction, _ = CalcMeridian(Frame, Lines, Start, BodyAxisVector(Start, Finish))
    return Replace(Definition, AxisOrigin=Start, AxisDirection=SpaceVector(*Direction))


# signed prisms keep the selected source rim on the original sketch station
def RebuildBodyRev(
    DocValue: CadDocument,
    PlanValue: BodyRevPlan,
    Binding: BodyAxisEdit,
    SourceSketch: Sketch,
    ProfileSketch: Sketch,
    SourceFrame: Transform,
    ProfileFrame: Transform,
    DepthMm: float,
    AlongRad: float,
) -> CadDocument:
    SeedStep, Creator, ProfileStep, Feature = DocValue.feature_timeline
    Definition = Feature.definition
    if not isinstance(Definition, AngularRevolve):
        raise ValueError("FreeCAD editable body axis Revolve source definition changed")
    LineRing = GetEditRing(Creator, SourceSketch)
    if LineRing is None:
        raise ValueError("FreeCAD editable body axis source ring changed topology")
    SeedBody, RevBody = DocValue.bodies
    SeedGeom = BuildEditSolid(SeedBody.id, SourceFrame, LineRing, DepthMm)
    EdgeId = FindSeedEdge(Binding.LineId, SeedGeom[0], SourceSketch, DepthMm)
    Start, Finish = ReadEditedAxis(SourceSketch, SourceFrame, Binding)
    Updated = ReadNewAxis(
        Feature, Definition, ProfileSketch, ProfileFrame, Start, Finish
    )
    Interval = GetAngleSpan(AlongRad, None, Updated.SideMode)
    if Interval[1] - Interval[0] > FullTurn:
        raise ValueError("FreeCAD editable body axis Revolve exceeds one turn")
    Feature = Replace(Feature, definition=Updated)
    RevGeom = BuildRevGeom(
        RevBody.id, Feature, Updated, Interval, ProfileSketch, ProfileFrame
    )
    (PickValue,) = DocValue.selections
    if EdgeId != PlanValue.AxisEdgeId:
        PickValue = Replace(
            PickValue, path=(PickValue.path[0], SelectPathElem("edge", EdgeId))
        )
    Metadata = DocValue.metadata
    if DepthMm < 0.0 or (Start, Finish) != (PlanValue.AxisStart, PlanValue.AxisEnd):
        Metadata = StoreAxisEdit(Metadata, Binding)
    Edited = Replace(
        DocValue,
        feature_timeline=(SeedStep, Creator, ProfileStep, Feature),
        selections=(PickValue,),
        bodies=(
            Replace(SeedBody, topology=GetBodyTopology(SeedGeom)),
            Replace(RevBody, topology=GetBodyTopology(RevGeom)),
        ),
        brep=JoinRevModels((SeedGeom[0], RevGeom[0])),
        metadata=Metadata,
    )
    if Edited.validate():
        raise ValueError("FreeCAD editable body axis Revolve rebuild is invalid")
    return Edited
