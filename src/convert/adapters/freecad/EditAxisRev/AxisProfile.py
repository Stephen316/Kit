# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue

from convert.adapters.freecad.EditAxisRev.AxisPrimitives import (
    ReadAxisGeom,
    ReadAxisPoint,
)
from convert.adapters.freecad.EditRev.RevProfileProof import CheckRevMembers
from convert.adapters.freecad.EditRing.RingEndpoints import ReadRingEnds
from convert.adapters.freecad.EditRing.RingInputs import ReadRingEnts
from convert.formats.Fusion.Profiles.LineRing import OrderLineRing
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.VectorPlane import PlaneVector


# separate point ids are paired only through exactly joined selected profile neighbors
def ReadAxisProfile(
    FeatureValue: FeatureStep, SketchValue: Sketch
) -> tuple[tuple[str, str], ...]:
    CheckRevMembers(FeatureValue, SketchValue)
    Members, Entities = ReadRingEnts(SketchValue)
    MemberSet = set(Members)
    NativeMembers = FeatureValue.attributes["fusion.profile_native_members"]
    if not isinstance(NativeMembers, tuple):
        raise ValueError("FreeCAD editable sketch axis profile members are unresolved")
    Sources = tuple(
        Entities[Identity] for Identity in CastValue(tuple[str, ...], NativeMembers)
    )
    if OrderLineRing(Sources) != Members:
        raise ValueError("FreeCAD editable sketch axis source profile order disagrees")
    Points = {
        Identity: ReadAxisPoint(Value)
        for Identity, Value in Entities.items()
        if Identity not in MemberSet
    }
    Endpoints: list[tuple[str, str]] = []
    for Identity in Members:
        Value = Entities[Identity]
        LineValue = ReadAxisGeom(Value, Construction=False)
        Start, Finish = ReadRingEnds(Value)
        if Points.get(Start) != LineValue.start or Points.get(Finish) != LineValue.end:
            raise ValueError(
                "FreeCAD editable sketch axis profile endpoint provenance disagrees"
            )
        Endpoints.append((Start, Finish))
    UsedIds = {Identity for EndpointPair in Endpoints for Identity in EndpointPair}
    Other = tuple(
        Value for Identity, Value in Points.items() if Identity not in UsedIds
    )
    if Other and Other != (PlaneVector(0.0, 0.0),):
        raise ValueError(
            "FreeCAD editable sketch axis profile has unrelated point geometry"
        )
    return JoinAxisProfile(tuple(Endpoints), Points)


# ordered corner pairs retain both native points without collapsing either identity
def JoinAxisProfile(
    Endpoints: tuple[tuple[str, str], ...], Points: dict[str, PlaneVector]
) -> tuple[tuple[str, str], ...]:
    First, Current = Endpoints[0]
    Pairs: list[tuple[str, str]] = []
    for Start, Finish in Endpoints[1:]:
        if Points[Current] == Points[Finish] and Points[Current] != Points[Start]:
            Start, Finish = Finish, Start
        if Points[Current] != Points[Start] or Points[Start] == Points[Finish]:
            raise ValueError(
                "FreeCAD editable sketch axis profile endpoints do not connect"
            )
        if Current != Start:
            Pairs.append((Current, Start))
        Current = Finish
    if Points[Current] != Points[First]:
        raise ValueError("FreeCAD editable sketch axis profile does not close")
    if Current != First:
        Pairs.append((Current, First))
    return tuple(Pairs)
