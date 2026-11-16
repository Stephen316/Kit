# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.PlaneBasis import KUnitRows, MatrixAxes
from convert.adapters.solidworks.Resolved.Circular.Boss import ReadRoundBoss
from convert.adapters.solidworks.Resolved.Circular.Records import (
    CircularBoss,
    CircularSupport,
)
from convert.adapters.solidworks.Sketch.CircularRecords import (
    RoundDiameter,
    CircularDisplay,
    CircularHeader,
    CircularMember,
    CircularOrigin,
    CircularPoint,
)
from convert.adapters.solidworks.Resolved.Circular.Profile import (
    ReadArcProfile,
    ReadRoundRegion,
)
from convert.adapters.solidworks.Resolved.OriginProfile import OriginProfile, ReadOrigin
from convert.adapters.solidworks.Resolved.PrincipalDatum import PrincipalDatum
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix
from convert.adapters.solidworks.Sketch.CircularDisplay import ReadRadialView
from convert.adapters.solidworks.Sketch.CircularMembers import (
    CircularCursor,
    ReadCircle,
    ReadDiameter,
    ReadViewPrefix,
    ReadOriginJoin,
    ReadPoints,
)


# neutral projection receives a complete single circular feature chain and original spans
@Dataclass(frozen=True, slots=True)
class CircularPart:
    Profile: CircularHeader
    Datum: PrincipalDatum
    Origin: OriginProfile
    Points: list[CircularPoint]
    Circle: CircularMember
    Diameter: RoundDiameter
    Coincidence: CircularOrigin
    Display: CircularDisplay
    Support: CircularSupport
    Boss: CircularBoss


# open the selected generation and retain the actual earlier typed datum
def OpenCircular(
    ConfigData: bytes, Resolved: bytes, Generation: int
) -> tuple[CircularCursor, CircularHeader, OriginProfile, PrincipalDatum]:
    ConfigMap, ConfigWalk = ReadOrdinaryMap(ConfigData, Generation)
    RequireArch(
        ConfigWalk["atom_count"] == 1 and sum(map(len, ConfigWalk["regions"])) == 1,
        True,
        "expected one archived body atom and region",
    )
    Parent = OpenResolved(Resolved, ConfigMap, 19)
    Front = ReadSysPrefix(Parent).Planes[0]
    Origin = ReadOrigin(Parent, Generation)
    RequireArch(Origin.Support.FeatureId, Front.FeatureId, "typed Origin datum")
    ProfileStart = Parent.Offset
    _, _, FeatureObject = Parent.TakePointer(("moProfileFeature_c",), KDefinitionKind)
    _ = Parent.TakePointer(("moNodeName_c",), KClassRefKind)
    NameValue, FeatureId, _ = ReadProfileHead(Parent, (0x40000000, 0xC0000000))
    _, _, SketchObject = Parent.TakePointer(("sgSketch",), KClassRefKind)
    return (
        CircularCursor(Parent),
        {
            "name": NameValue,
            "feature_id": FeatureId,
            "feature_node": FeatureObject,
            "feature_start": ProfileStart,
            "sketch_node": SketchObject,
        },
        Origin,
        Front,
    )


# read geometry editing relations and the terminal positive blind boss as one chain
def ReadRoundModel(ConfigData: bytes, Resolved: bytes, Generation: int) -> CircularPart:
    Cursor, Profile, Origin, Datum = OpenCircular(ConfigData, Resolved, Generation)
    Points = ReadPoints(Cursor)
    Circle = ReadCircle(Cursor, Points)
    Diameter = ReadDiameter(Cursor, Circle)
    Coincidence = ReadOriginJoin(Cursor, Points, Circle, Origin)
    Prefix = ReadViewPrefix(Cursor)
    Display = ReadRadialView(Cursor, Profile, Diameter)
    _ = ReadRoundRegion(Cursor, Circle)
    Returned = ReadArcProfile(Cursor, Profile, Circle, Origin)
    RequireArch(
        (
            Returned["support"]["feature"],
            Returned["support"]["axes"],
            Origin.Support.ShiftScale,
        ),
        (
            Datum.FeatureId,
            MatrixAxes(Datum.Geometry.BasisValue or KUnitRows),
            Datum.Geometry.ShiftScale,
        ),
        "circular profile frame agrees with the reached principal support",
    )
    BossValue = ReadRoundBoss(Cursor, Profile, Returned, Circle, Points, Origin)
    return CircularPart(
        Profile,
        Datum,
        Origin,
        Points,
        Circle,
        Diameter,
        Coincidence,
        {**Prefix, **Display},
        Returned["support"],
        BossValue,
    )
